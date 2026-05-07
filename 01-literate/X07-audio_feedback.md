---
version: "2.0"
generated: "2026-05-06"
---

# Audio Feedback (Appendix)

`audio_feedback.py` provides a single lightweight beep function for voice state transitions. It synthesizes a short sine wave and plays it through the configured ALSA output device.

## Design: aplay over PyAudio

The initial implementation used PyAudio to play tones. PyAudio's device indexing does not map 1:1 to ALSA card numbers, and its initialization floods stderr with ALSA/JACK enumeration messages. More importantly, playing to the wrong device index silently produces no sound.

The replacement uses `aplay` — the same path used by Piper TTS for speech output:

```python
def beep(frequency: int = 880, duration: float = 0.15, device_index: int = 0) -> None:
    alsa_device = os.environ.get("SPEECH_ALSA_DEVICE", "")
    sample_rate = 16000
    n = int(sample_rate * duration)
    samples = bytearray(n * 2)
    amplitude = 0.2
    for i in range(n):
        s = int(math.sin(2 * math.pi * frequency * i / sample_rate) * 32767 * amplitude)
        struct.pack_into("<h", samples, i * 2, max(-32768, min(32767, s)))

    cmd = ["aplay", "-q", "-f", "S16_LE", "-r", str(sample_rate), "-c", "1"]
    if alsa_device:
        cmd.extend(["-D", alsa_device])
    try:
        subprocess.run(cmd, input=bytes(samples), check=False, capture_output=True)
    except Exception as exc:
        import sys
        print(f"beep: aplay failed: {exc}", file=sys.stderr)
```

`SPEECH_ALSA_DEVICE` is the same environment variable consumed by `speech_output_node`, so both speech and beeps route to the same output device without separate configuration.

## Signal Generation

The sine wave is generated sample-by-sample using `struct.pack_into` directly into a `bytearray`. This avoids a numpy dependency. Amplitude is 20% of full scale — audible but not startling.

## Usage in VoiceInputNode

| Event | Frequency | Duration |
|-------|-----------|----------|
| Wake word detected | 880 Hz | 20 ms |
| Intent recognized | 330 Hz | 20 ms |
| Empty / unrecognized turn | 220 Hz | 150 ms |

The `device_index` parameter is retained for API compatibility but unused; ALSA device selection is done via the environment variable.

## Observations

- Beep is synchronous — it blocks the voice loop for `duration` seconds. For the 20 ms beeps this is negligible; the 150 ms failure beep adds latency.
- `check=False` and the broad `except Exception: pass` ensure a broken audio device never crashes the voice pipeline.
