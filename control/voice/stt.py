#!/usr/bin/env python3
"""Speech-to-text using Vosk."""

import json
import os

from control.voice.intent_mapper import VOSK_COMMANDS


def _load_deps():
    try:
        import pyaudio
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise RuntimeError(
            "Install voice deps: pip install vosk pyaudio"
        ) from exc
    return pyaudio, KaldiRecognizer, Model


class SpeechTranscriber:
    CHUNK = 1600  # 100ms at 16kHz — smaller chunks = faster silence detection
    MAX_RECORD_SECONDS = 5

    DEFAULT_MODEL_PATH = os.path.expanduser("~/models/vosk-model-small-en-us-0.15")

    def __init__(self, device_index: int = 0, model_path: str = ""):
        self._pyaudio, self._KaldiRecognizer, Model = _load_deps()
        path = model_path or os.environ.get("VOSK_MODEL_PATH") or self.DEFAULT_MODEL_PATH
        self._model = Model(path)
        self._rec = self._KaldiRecognizer(self._model, 16000, VOSK_COMMANDS)
        self._pa = self._pyaudio.PyAudio()
        self._device_index = device_index

    NO_SPEECH_TIMEOUT_S = 2.0

    def transcribe(self) -> str:
        """Record until Vosk detects end of utterance or timeout, return text.

        Returns empty string if no speech detected within NO_SPEECH_TIMEOUT_S.
        """
        self._rec.Reset()
        stream = self._pa.open(
            rate=16000, channels=1, format=self._pyaudio.paInt16,
            input=True, frames_per_buffer=self.CHUNK,
            input_device_index=self._device_index,
        )
        try:
            max_frames = int(16000 / self.CHUNK * self.MAX_RECORD_SECONDS)
            no_speech_frames = int(16000 / self.CHUNK * self.NO_SPEECH_TIMEOUT_S)
            for i in range(max_frames):
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                if self._rec.AcceptWaveform(data):
                    result = json.loads(self._rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        return text
                if i == no_speech_frames - 1:
                    partial = json.loads(self._rec.PartialResult()).get("partial", "")
                    if not partial:
                        return ""
            return json.loads(self._rec.FinalResult()).get("text", "").strip()
        finally:
            stream.stop_stream()
            stream.close()

    def close(self) -> None:
        self._pa.terminate()
