#!/usr/bin/env python3
"""Wake word detection using openWakeWord."""

import os
import time
from typing import Callable


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


def _default_model_path() -> str:
    import openwakeword as oww
    return os.path.join(os.path.dirname(oww.__file__),
                        "resources", "models", "hey_jarvis_v0.1.onnx")


class WakeWordDetector:
    FRAME_LENGTH = 1280
    THRESHOLD = 0.5
    DEBOUNCE_S = 4.0

    def __init__(self, device_index: int = 0, model_path: str = ""):
        self._np, self._pyaudio, Model = _load_deps()
        path = model_path or os.environ.get("OWW_MODEL_PATH") or _default_model_path()
        self._model = Model(wakeword_model_paths=[path])
        self._pa = self._pyaudio.PyAudio()
        self._device_index = device_index
        self._stream = None
        self._last_wake = 0.0

    def start(self) -> None:
        self._stream = self._pa.open(
            rate=16000, channels=1, format=self._pyaudio.paInt16,
            input=True, frames_per_buffer=self.FRAME_LENGTH,
            input_device_index=self._device_index,
        )
        # flush buffered audio accumulated while stream was closed
        for _ in range(5):
            self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False)

    def stop(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

    def wait_for_wake(self, ok_fn: Callable[[], bool] = lambda: True) -> bool:
        """Block until wake word detected or ok_fn() returns False."""
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

    def close(self) -> None:
        self.stop()
        self._pa.terminate()
