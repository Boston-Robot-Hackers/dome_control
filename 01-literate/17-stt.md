---
version: "1.0"
generated: "2026-05-06"
---

# SpeechTranscriber

`stt.py` owns the speech-to-text half of the voice loop. It turns command audio
into text using Vosk, with the grammar and model path selected by the voice
runtime configuration.

## Vocabulary and Model Path

The transcriber no longer assumes only one hardcoded grammar. Instead it accepts
the grammar from the caller and turns it into the JSON format Vosk expects.

```python
def _grammar_json(grammar: list[str] | tuple[str, ...] | str | None) -> str:
    if grammar is None:
        return VOSK_COMMANDS
    if isinstance(grammar, str):
        phrases = [item.strip() for item in grammar.split(",") if item.strip()]
    else:
        phrases = [str(item).strip() for item in grammar if str(item).strip()]
    if "[unk]" not in phrases:
        phrases.append("[unk]")
    return json.dumps(phrases)
```

That makes the recognizer compatible with the tuned command set in
`control.voice.runtime` while still allowing the older vocabulary constant to
serve as the fallback.

The model path is also configurable through the runtime's `vosk_model` value,
with short keys like `small` expanded through the local path map.

## Recording Loop

```python
def transcribe(self) -> str:
    self._rec.Reset()
    stream = self._pa.open(
        rate=16000, channels=1, format=self._pyaudio.paInt16,
        input=True, frames_per_buffer=self.CHUNK,
        input_device_index=self._device_index,
    )
    try:
        ...
```

The transcriber opens a fresh PyAudio stream per command. That matches the
command-turn shape of the voice pipeline and keeps the wake-word stream and STT
stream separate.

The loop has three useful exits:

1. Vosk detects end of utterance and returns a non-empty result.
2. Silence persists long enough that there is no partial speech, so the function
   returns an empty string.
3. The maximum recording window is reached and a final result is forced.

## Observations

- The object is still deliberately small; the runtime now owns the higher-level
  command turn flow.
- A future improvement would be to make the silence timeout and record window
  part of the shared runtime dataclass instead of fixed class attributes.
