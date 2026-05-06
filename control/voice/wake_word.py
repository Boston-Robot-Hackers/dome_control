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


_UTILITY_MODELS = {"embedding_model", "melspectrogram", "silero_vad"}


def _resolve_model_path(name_or_path: str) -> str:
    if os.path.isabs(name_or_path) and os.path.exists(name_or_path):
        return name_or_path

    import openwakeword as oww

    models_dir = os.path.join(os.path.dirname(oww.__file__), "resources", "models")
    if not os.path.isdir(models_dir):
        return _default_model_path()

    candidates = [
        fname for fname in os.listdir(models_dir)
        if fname.endswith(".onnx") and os.path.splitext(fname)[0] not in _UTILITY_MODELS
    ]
    for fname in candidates:
        stem = os.path.splitext(fname)[0]
        if stem == name_or_path or stem.startswith(name_or_path + "_"):
            return os.path.join(models_dir, fname)
    return _default_model_path()


class WakeWordDetector:
    FRAME_LENGTH = 1280
    THRESHOLD = 0.5
    DEBOUNCE_S = 4.0

    def __init__(
        self,
        device_index: int = 0,
        model_path: str = "",
        wake_word: str = "hey_jarvis",
        threshold: float | None = None,
        wake_hits: int = 1,
    ):
        self._np, self._pyaudio, Model = _load_deps()
        configured_model = model_path or os.environ.get("OWW_MODEL_PATH")
        path = configured_model or _resolve_model_path(wake_word)
        self._model = Model(wakeword_model_paths=[path])
        self._pa = self._pyaudio.PyAudio()
        self._device_index = device_index
        self._stream = None
        self._last_wake = 0.0
        self._threshold = self.THRESHOLD if threshold is None else threshold
        self._wake_hits_required = max(1, wake_hits)

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
        wake_hits = 0
        while ok_fn():
            audio = self._np.frombuffer(
                self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False),
                dtype=self._np.int16,
            )
            score = list(self._model.predict(audio).values())[0]
            now = time.time()
            if score <= self._threshold:
                wake_hits = 0
                continue
            wake_hits += 1
            if wake_hits >= self._wake_hits_required and (
                now - self._last_wake
            ) > self.DEBOUNCE_S:
                self._last_wake = now
                return True
        return False

    def close(self) -> None:
        self.stop()
        self._pa.terminate()
