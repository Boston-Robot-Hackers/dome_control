---
version: "1.0"
generated: "2026-05-04"
---

# SpeechTranscriber

`stt.py` records audio after wake word detection and converts it to text using Vosk, a local offline speech recogniser.

## Why Vosk

Vosk runs entirely offline — no API keys, no network round-trips, no cloud dependency. This matters for a robot that may operate in environments without internet. The small English model (`vosk-model-small-en-us-0.15`) fits in ~50MB and runs in real time on a Raspberry Pi.

## Constrained Grammar

```python
self._rec = self._KaldiRecognizer(self._model, 16000, VOSK_COMMANDS)
```

`KaldiRecognizer` is constructed with `VOSK_COMMANDS` (the JSON vocab list from `intent_mapper.py`). Vosk restricts its search to this vocabulary, which improves accuracy on short command phrases at the cost of rejecting free-form speech.

## Recording Loop

```python
def transcribe(self) -> str:
    self._rec.Reset()
    stream = self._pa.open(rate=16000, channels=1, format=paInt16,
                           input=True, frames_per_buffer=self.CHUNK, ...)
    try:
        max_frames = int(16000 / self.CHUNK * self.MAX_RECORD_SECONDS)  # 5s
        no_speech_frames = int(16000 / self.CHUNK * self.NO_SPEECH_TIMEOUT_S)  # 2s

        for i in range(max_frames):
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            if self._rec.AcceptWaveform(data):          # end of utterance detected
                result = json.loads(self._rec.Result())
                text = result.get("text", "").strip()
                if text:
                    return text
            if i == no_speech_frames - 1:               # early silence exit
                partial = json.loads(self._rec.PartialResult()).get("partial", "")
                if not partial:
                    return ""

        return json.loads(self._rec.FinalResult()).get("text", "").strip()
    finally:
        stream.stop_stream()
        stream.close()
```

Three exit paths:

1. **Utterance end**: `AcceptWaveform` returns `True` when Vosk detects a speech boundary (silence after speech). Returns the recognised text immediately.
2. **Silence timeout**: After `NO_SPEECH_TIMEOUT_S = 2.0s`, if there's no partial result, returns empty string. Prevents waiting 5 seconds when the user said nothing.
3. **Max duration**: After `MAX_RECORD_SECONDS = 5.0s`, forces a final result.

`CHUNK = 1600` (100ms at 16kHz) is the comment says "smaller chunks = faster silence detection." Each `AcceptWaveform` call processes one chunk, so 100ms chunks give 100ms silence detection granularity.

## Stream Lifecycle

The audio stream is opened at the start of `transcribe()` and closed in the `finally` block — not kept open between calls. This is different from `WakeWordDetector`, which has explicit `start()`/`stop()` methods. The difference reflects how they're used: wake word detection runs a continuous loop, STT is a one-shot capture.

## Observations

- The recorder opens a fresh PyAudio stream on every `transcribe()` call. On some systems, stream open/close has measurable latency (10-50ms). If responsiveness is critical, keeping the stream open would help.
- `self._rec.Reset()` at the start clears state from any previous partial result. This is necessary because `KaldiRecognizer` is reused across calls.
- The 2-second silence timeout uses frame counting rather than wall clock time. This is robust to variable system load but could be simplified with `time.time()`.
