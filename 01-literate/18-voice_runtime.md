---
version: "1.0"
generated: "2026-05-06"
---

# VoiceRuntime

`control/voice/runtime.py` is the shared non-ROS voice runtime. It collects the
parameters copied from `~/tune`, runs the wake-word and STT helpers, and returns
a structured turn result that the ROS node can consume.

The point of this module is not flexibility for its own sake. It is a single
place where the tuned voice parameters are visible, where the production audio
flow is implemented, and where Pi-only smoke testing can happen without ROS.

## Tuned Parameters

```python
TUNED_VOICE_PARAMETERS = {
    "capture_card": 0,
    "playback_card": 0,
    "stream_settings": {
        "wake_word": "alexa",
        "threshold": 0.3,
        "wake_hits": 1,
        "live_filter": True,
        "vosk_model": "small",
        "grammar": list(DEFAULT_GRAMMAR),
    },
    "sox_chain": {
        "highpass": 120,
        "lowpass": 4000,
    },
}
```

This block is the hand-editable handoff point from `tune`. The code can use it
directly, or it can load a tune YAML file for comparison. The important thing is
that the production parameters are obvious and easy to paste.

## Runtime Shape

The runtime is a small orchestration object:

```python
class VoiceRuntime:
    def next_turn(self, ok_fn: Callable[[], bool] = lambda: True, ...):
        ...
```

`next_turn()` owns the whole voice turn:

1. Open or reuse the capture stream.
2. Wait for wake detection.
3. Capture the command.
4. Return a `VoiceTurn` dataclass with transcript text and timing metadata.

That return value is intentionally plain. The ROS adapter only needs to know
what was recognized and whether the turn was empty.

## Audio Processing

The runtime embeds the audio helpers that were validated in `tune`:

```python
class LiveBandpass:
    def process(self, samples: np.ndarray) -> np.ndarray:
        ...

def read_mono_chunk(stream, n_samples: int = CHUNK, live_filter=None) -> np.ndarray | None:
    ...
```

The capture path does three things before recognition:

1. Convert stereo `arecord` output to mono.
2. Remove DC offset from each chunk.
3. Apply optional live highpass/lowpass filtering.

That keeps the runtime close to the tuned Pi audio path without pulling the
`tune` package into `control`.

## Wake And Command Flow

```text
open_arecord -> wait_for_wake -> capture_command -> VoiceTurn
```

The wake stage returns score and timing data so the smoke test can report
useful metrics. The command stage strips the wake word from the recognized text
before returning the final transcript.

## Smoke Test

The module exposes a simple entry point:

```bash
python3 -m control.voice.runtime --trials 5
```

That is meant for Pi hardware, not unit tests. It gives a quick read on wake
hits, empty turns, and latency using the pasted tuning parameters.

## Observations

- The module is doing orchestration plus signal processing. That is acceptable
  here because the whole point is to have one place for the production voice
  behavior.
- If the voice contract grows, the next useful split would be to separate the
  audio helpers from the turn orchestration.
