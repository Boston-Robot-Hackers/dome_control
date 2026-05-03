# Voice Input Pipeline

## What It Does and Why

The voice pipeline lets the dome robot accept spoken commands offline — no cloud,
no internet dependency. Say "Hey Jarvis", speak a command, and a structured intent
JSON appears on the ROS2 `/intent` topic for `behavior_manager_node` to act on.

The design splits responsibility cleanly across four modules:

```
wake_word.py       — continuous listening, fires on "Hey Jarvis"
stt.py             — records and transcribes the command
intent_mapper.py   — maps transcript text to intent dict
voice_input_node.py — ROS2 shell that wires the three together
```

None of the first three know about ROS2. All audio and ML logic is pure Python,
unit-testable without a running ROS2 environment.

## The Wake Word Detector

The hardest constraint in always-on voice is CPU budget. `WakeWordDetector` uses
[openWakeWord](https://github.com/dscripka/openWakeWord) with its bundled
`hey_jarvis_v0.1.onnx` model — a tiny ONNX inference graph that scores every 80ms
audio frame. On a Pi 5 this runs at ~5% CPU, leaving the rest for navigation and
vision.

Heavy imports (`numpy`, `pyaudio`, `openwakeword`) are deferred to `__init__` via
`_load_deps()`. This keeps the module importable in test environments where the
voice deps are not installed.

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

The detector reads 1280-sample frames (80ms at 16kHz) — the native frame size
the openWakeWord model expects. Each frame is scored; when the score crosses 0.5
the wake word has been detected.

```python
score = list(self._model.predict(audio).values())[0]
if score > self.THRESHOLD and (now - self._last_wake) > self.DEBOUNCE_S:
    self._last_wake = now
    return True
```

Two subtleties worth noting:

**Debounce.** A single spoken "Hey Jarvis" produces many consecutive high-score
frames — the model's internal 30-frame prediction buffer stays hot for several
seconds. Without debouncing, `wait_for_wake` would return dozens of times per
utterance. `_last_wake` is an *instance* variable (not local) so debounce persists
across successive calls — an easy mistake that breaks the whole pipeline.

**Buffer flush on start.** When the audio stream is reopened after STT finishes,
the ALSA buffer contains stale audio from the STT window. Five frames of
throwaway reads drain this before real detection begins:

```python
for _ in range(5):
    self._stream.read(self.FRAME_LENGTH, exception_on_overflow=False)
```

**Model reset.** `self._model.reset()` clears the internal prediction buffer at
the top of every `wait_for_wake` call, preventing a residual high score from the
previous detection triggering immediately.

## Speech-to-Text

`SpeechTranscriber` uses [Vosk](https://alphacephei.com/vosk/) with the small
English model (`vosk-model-small-en-us-0.15`, ~40MB). Two design choices define
its behavior:

**Constrained vocabulary.** Rather than free-form transcription, Vosk is given an
explicit list of recognized phrases. This list — `VOSK_COMMANDS` — is owned by
`intent_mapper.py` (the single source of truth for what commands exist) and
imported into `stt.py`. Free transcription of arbitrary speech is unnecessary and
degrades accuracy for a finite command set.

**One recognizer, many transcriptions.** `KaldiRecognizer` is expensive to
construct — it builds an FST grammar from `VOSK_COMMANDS` at creation time. The
recognizer is created once at `__init__` and `Reset()` between calls:

```python
self._rec = self._KaldiRecognizer(self._model, 16000, VOSK_COMMANDS)

def transcribe(self) -> str:
    self._rec.Reset()
    ...
```

Early in development this was created per-call, causing a grammar rebuild on every
utterance — visible in the logs as `UpdateGrammarFst` / `Estimate` / `OutputToFst`
lines appearing repeatedly and adding ~2 seconds of latency.

**Early exit on silence.** `AcceptWaveform` returns `True` when Vosk detects the
end of an utterance (silence after speech). This is used to return immediately
rather than waiting out the full 5-second window:

```python
if self._rec.AcceptWaveform(data):
    result = json.loads(self._rec.Result())
    text = result.get("text", "").strip()
    if text:
        return text
```

**No-speech timeout.** If `PartialResult` is still empty after 2 seconds, the
user said nothing — return early rather than waiting 5 seconds:

```python
if i == no_speech_frames - 1:
    partial = json.loads(self._rec.PartialResult()).get("partial", "")
    if not partial:
        return ""
```

**Device conflict.** `WakeWordDetector` and `SpeechTranscriber` cannot both hold
an open input stream simultaneously on the ReSpeaker HAT (the device rejects the
second open). The node alternates: wake word stream open → detect → close → STT
stream open → transcribe → close → repeat.

## Intent Mapping

`intent_mapper.py` is the only module with no external dependencies — pure Python,
no audio, no ROS2. It owns two things:

1. `VOSK_COMMANDS` — the constrained vocabulary list imported by `stt.py`
2. `map_intent()` — text → intent dict

```
VOSK_COMMANDS (single source of truth)
    ↓ imported by
stt.py  →  transcribe()  →  text  →  map_intent()  →  intent dict
```

The mapping uses substring matching ordered from most-specific to least-specific.
"go home" must be checked before "home" to avoid the shorter phrase shadowing the
longer one. "where are you" before "where" for the same reason.

```python
if _contains(t, "go home", "return home", "come back", "home"):
    return {"name": "return_home", ...}
```

Slot extraction for `count_objects` scans a fixed list of known object types:

```python
OBJECT_TYPES = ["can", "bottle", "person", "chair", "table", "ball", "cup", "box"]

def _extract_object(text: str) -> Optional[str]:
    for obj in OBJECT_TYPES:
        if obj in text:
            return obj
    return None
```

## The ROS2 Node

`voice_input_node.py` is a thin shell. It owns no logic — it creates the three
objects, runs the loop, and publishes results.

```
while rclpy.ok():
    detector.start()
    wait_for_wake()        →  high beep (880Hz, 20ms)
    detector.stop()
    transcribe()           ←  STT window opens
    map_intent(text)
    publish /intent        →  low beep (330Hz, 20ms)
                           →  or speak("say again") if no match
```

Audio feedback — two short beeps — signals state transitions without requiring
the user to watch a screen. The high beep means "I'm listening"; the low beep
means "done, waiting for next wake word". Implemented in `audio_feedback.py` using
a numpy sine wave played through pyaudio's output path.

Published topics:
- `/intent` — `std_msgs/String` JSON, consumed by `behavior_manager_node`
- `/voice/state` — `IDLE` / `LISTENING` / `PROCESSING`, for display/LED nodes
- `/announcement` — text for future `speech_output_node` (Piper TTS)

## Observations and Improvements

**Wake word accuracy.** openWakeWord's `hey_jarvis_v0.1` model is a community
model, not professionally trained. False positive rate is higher than Picovoice
Porcupine. A custom-trained wake word with more positive samples would improve
reliability.

**STT accuracy for short commands.** The small Vosk model occasionally mishears
multi-word phrases. The constrained vocabulary helps significantly. The medium
model (`vosk-model-en-us-0.22-lgraph`, ~130MB) supports constrained vocab and
would improve accuracy at the cost of load time.

**Device sharing.** Opening and closing the audio stream for each wake/STT cycle
adds ~100ms overhead per cycle. A better design would use a single always-open
stream with a ring buffer, routing frames to the active consumer (wake word or
STT) based on state — eliminating stream open/close latency entirely.

**`speak()` is a placeholder.** `espeak-ng` produces intelligible but robotic
speech. Phase 6 replaces it with `speech_output_node` using Piper TTS through
the ReSpeaker HAT's onboard Class-D amplifier — the same hardware path already
proven for ALSA playback.

**Intent mapper is not fuzzy.** Substring matching fails if Vosk transcribes "go
home" as "go poem" (out-of-vocabulary noise). Adding edit-distance matching or
mapping common transcription errors would make the mapper more robust without
adding ML complexity.

**No slot validation.** `count_objects` silently omits the `object_type` slot if
no known object word appears in the transcript. `behavior_manager_node` should
handle the missing-slot case gracefully (ask for clarification or count all
objects).
