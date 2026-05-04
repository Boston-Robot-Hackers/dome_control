---
version: "1.0"
generated: "2026-05-04"
---

# WakeWordDetector

`wake_word.py` continuously listens for a wake phrase ("Hey Jarvis") using openWakeWord. When detected, it signals the voice pipeline to start listening for a command.

## Lazy Dependency Loading

```python
def _load_deps():
    try:
        import numpy as np
        import pyaudio
        from openwakeword.model import Model
    except ImportError as exc:
        raise RuntimeError("Install voice deps: pip install openwakeword pyaudio numpy") from exc
    return np, pyaudio, Model
```

Dependencies are imported inside a function rather than at module top-level. This allows the rest of the control package to import `wake_word` on systems without audio libraries installed — the error only surfaces when `WakeWordDetector()` is constructed.

## Detection Loop

```python
def wait_for_wake(self, ok_fn: Callable[[], bool] = lambda: True) -> bool:
    self._model.reset()
    while ok_fn():
        audio = self._np.frombuffer(
            self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False),
            dtype=self._np.int16,
        )
        score = list(self._model.predict(audio).values())[0]
        now = time.time()
        if score > self.THRESHOLD and (now - self._last_wake) > self.DEBOUNCE_S:
            self._last_wake = now
            return True
    return False
```

`ok_fn` is a callable checked each iteration — `rclpy.ok` in production, `lambda: True` in tests. This lets the loop terminate cleanly when the ROS2 context shuts down without requiring a separate thread or event.

The model is reset at the start of each `wait_for_wake` call to clear any residual scores from the previous detection window.

## Debouncing

```python
THRESHOLD = 0.5
DEBOUNCE_S = 4.0
```

After a wake word fires, the detector ignores further detections for 4 seconds. This prevents the robot from repeatedly triggering on the wake word audio that leaks back from its own speaker during TTS playback.

## Buffered Audio Flush

```python
def start(self) -> None:
    self._stream = self._pa.open(...)
    for _ in range(5):
        self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False)
```

When the audio stream is re-opened (after being closed at the end of a listening cycle), PyAudio's internal ring buffer may contain old audio that accumulated while the stream was closed. Reading and discarding 5 frames (5 × 1280 samples at 16kHz ≈ 400ms) flushes this stale audio.

## Observations

- `FRAME_LENGTH = 1280` matches openWakeWord's expected input size (80ms at 16kHz). This is a fixed model requirement; changing it would break detection.
- The model path falls back to the default Hey Jarvis ONNX model bundled with the `openwakeword` package. A custom wake phrase requires training a new model and setting `OWW_MODEL_PATH`.
- `wait_for_wake` blocks indefinitely (until `ok_fn()` returns False or a wake word fires). The calling code in `VoiceInputNode.main` handles the `not detected` return by breaking the main loop cleanly.
