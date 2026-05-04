---
version: "1.0"
generated: "2026-05-04"
---

# SpeechOutputNode

`speech_output_node.py` subscribes to `/announcement` and converts text to speech using Piper TTS and ALSA playback. It is the voice of the robot.

## Pipeline

```
/announcement (AnnouncementMsg)
        ↓ on_announcement
  SpeechOutputNode
        ↓ synthesize_to_wav (Piper)
  /tmp/speech-output-XXXX.wav
        ↓ apply_wav_gain (optional)
  /tmp/speech-output-YYYY.wav
        ↓ play_wav (aplay)
  speaker output
        ↓ cleanup temp files
```

## Piper TTS Integration

```python
def synthesize_to_wav(text, wav_path, piper_bin, model_path, length_scale):
    cmd = [piper_bin, "--model", model_path, "--output_file", wav_path,
           "--length_scale", str(length_scale), "--quiet"]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True, capture_output=True)
```

Piper is invoked as an external subprocess. Text is passed on stdin; the WAV file is written to a temp path. `--quiet` suppresses Piper's progress output. `length_scale` controls speech speed (>1.0 = slower, <1.0 = faster); the default is 1.25 — slightly slower than natural speed for clarity in a robot environment.

## Volume Control via PCM Gain

Piper has no built-in volume control. Instead, the node applies a software gain to the raw PCM samples:

```python
def _scale_pcm_frames(frames: bytes, sample_width: int, gain: float) -> bytes:
    max_value = (1 << (sample_width * 8 - 1)) - 1
    min_value = -(1 << (sample_width * 8 - 1))
    for offset in range(0, len(frames), sample_width):
        sample = struct.unpack_from(fmt, frames, offset)[0]
        adjusted = max(min(int(sample * gain), max_value), min_value)
        scaled.extend(struct.pack(fmt, adjusted))
    return bytes(scaled)
```

The default `SPEECH_GAIN = 0.35` attenuates the output to 35% of full scale. This is a workaround for Piper models that generate audio at a high peak amplitude that would clip on the robot's speaker. Gain is applied in pure Python with `struct.pack/unpack` — not fast, but audio synthesis time (seconds) dominates over gain application time (milliseconds).

## Environment Variable Configuration

All tunable parameters come from environment variables with sensible defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PIPER_BIN` | `"piper"` | Path to Piper binary |
| `PIPER_MODEL_PATH` | `""` | Required — raises RuntimeError if empty |
| `SPEECH_ALSA_DEVICE` | `""` | ALSA device string (e.g., `"hw:1,0"`) |
| `SPEECH_TMP_DIR` | `tempfile.gettempdir()` | Directory for temp WAV files |
| `SPEECH_GAIN` | `"0.35"` | PCM amplitude multiplier |
| `PIPER_LENGTH_SCALE` | `"1.25"` | Speech rate (>1 = slower) |

`PIPER_MODEL_PATH` is the only genuinely required variable — `synthesize_to_wav` raises `RuntimeError` at call time if it's empty.

## Temp File Cleanup

```python
def speak_text(self, text: str) -> None:
    wav_path = self._make_wav_path()
    gained_path = None
    try:
        synthesize_to_wav(...)
        if self.speech_gain != 1.0:
            gained_path = self._make_wav_path()
            apply_wav_gain(wav_path, gained_path, self.speech_gain)
            playback_path = gained_path
        play_wav(playback_path, ...)
    finally:
        for path in (wav_path, gained_path):
            if path:
                try: os.remove(path)
                except FileNotFoundError: pass
```

Both temp files (original and gained) are cleaned up in `finally`. The `FileNotFoundError` suppression handles the case where synthesis failed before the file was created.

## Observations

- `speak_text` blocks until Piper finishes synthesis and `aplay` finishes playback. During this time, `/announcement` messages queue in the ROS2 subscriber buffer (depth=10). If multiple announcements arrive while the robot is speaking, they will be spoken sequentially. There is no skip, interrupt, or priority-based preemption.
- `_scale_pcm_frames` only supports sample widths 1, 2, and 4 bytes. Piper always outputs 16-bit (2-byte) WAV, so this is not a practical limitation.
- `parse_speech_gain` and `parse_length_scale` raise `ValueError` with descriptive messages. These are called in `__init__`, so a bad env var kills the node at startup with a clear error — good fail-fast behaviour.
