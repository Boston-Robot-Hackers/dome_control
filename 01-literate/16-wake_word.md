---
version: "1.0"
generated: "2026-05-06"
---

# WakeWordDetector

`wake_word.py` provides the wake-word half of the voice loop. It keeps the
openWakeWord dependency isolated behind a small class that can be configured at
construction time and used from the ROS adapter or from tests with injected
fakes.

## Dependency Isolation

```python
def _load_deps():
    try:
        import numpy as np
        import pyaudio
        from openwakeword.model import Model
    except ImportError as exc:
        raise RuntimeError(
            "Install voice deps: pip install openwakeword pyaudio numpy"
        ) from exc
    return np, pyaudio, Model
```

This lazy import pattern keeps the rest of `control` importable on machines that
do not have the voice stack installed. The error only appears when the wake-word
detector is actually constructed.

## Model Selection

The detector now accepts a wake-word name, threshold, and wake-hit count rather
than baking those values into the class. That makes it match the tuned voice
parameters exposed in `control.voice.runtime`.

```python
def _resolve_model_path(name_or_path: str) -> str:
    if os.path.isabs(name_or_path) and os.path.exists(name_or_path):
        return name_or_path

    import openwakeword as oww

    models_dir = os.path.join(os.path.dirname(oww.__file__), "resources", "models")
    ...
```

The resolver still supports either an explicit ONNX path or a short model name.
That keeps the detector useful for both the stock bundled model and custom tuned
models.

## Wake Detection

```python
def wait_for_wake(self, ok_fn: Callable[[], bool] = lambda: True) -> bool:
    self._model.reset()
    wake_hits = 0
    while ok_fn():
        audio = self._np.frombuffer(
            self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False),
            dtype=self._np.int16,
        )
        score = list(self._model.predict(audio).values())[0]
        ...
```

The detector requires a configured number of consecutive wake hits before it
fires. That matches the tuning workflow, where one threshold is not always
enough to eliminate chatter.

The `ok_fn` callback remains the shutdown hook. In production it is `rclpy.ok`;
in tests it can be a constant lambda.

## Stream Lifecycle

The stream is opened and closed explicitly with `start()` and `stop()`. That is
important because the wake-word loop is continuous, while the command capture
phase is separate and should own the microphone during its turn.

## Observations

- The detector still flushes a few frames after reopening the stream to avoid
  stale buffered audio.
- The code path is intentionally thin. All tuning now lives in the shared voice
  runtime configuration instead of this module.
