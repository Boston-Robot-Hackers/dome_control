# Tasks for Feature F04

## T01 — Install openWakeWord and validate on hardware
**Status**: done
**Description**: On the Pi, create/reuse `~/venvs/dome-voice`, install
`openwakeword pyaudio`, and run the Phase 3 test script from
`02-doc/voice-hardware-smoke-test.md`. Pass condition: saying "Hey Jarvis"
prints a detection event. Manual hardware step, no code change.

## T02 — Install Vosk and validate transcription
**Status**: done
**Description**: In dome-voice venv, install `vosk` and download
`vosk-model-small-en-us`. Record a short phrase via the ReSpeaker mic and
confirm Vosk transcribes it correctly. Manual hardware step, no code change.

## T03 — Validate existing voice_input_node on hardware
**Status**: done
**Description**: Superseded by T04. Old Porcupine stub node was replaced entirely
by the openWakeWord + Vosk implementation in T04. No separate validation of the
old node needed.

## T04 — Replace voice_input_node with openWakeWord + Vosk
**Status**: done
**Description**: Rewrite `voice_input_node.py` to use openWakeWord for wake-word
detection and Vosk for STT. After "Hey Jarvis" fires, record audio until silence,
transcribe with Vosk, pass text to intent mapper, publish structured intent JSON
on `/intent`. `VOSK_MODEL_PATH` env var selects the model directory.

## T05 — Implement keyword/intent mapper
**Status**: done
**Description**: Write a pure Python `IntentMapper` class that takes a Vosk
transcript string and returns a structured intent dict matching the intent table
in `02-doc/control-architecture.md`. Use keyword/phrase matching (not ML).
Unrecognized input returns `None` (triggers "I didn't catch that"). Fully unit
testable without ROS2 or audio hardware.

## T06 — Implement voice state machine
**Status**: done
**Description**: Add the IDLE → LISTENING → PROCESSING → SPEAKING → IDLE state
machine to `voice_input_node`. Publish current state as a string on `/voice/state`
so display and LED nodes can subscribe later.

## T07 — Write tests
**Status**: done
**Description**: Unit tests for `IntentMapper` (known phrases → correct intents,
unknown phrase → None). Integration tests for `voice_input_node` mocking
openWakeWord and Vosk. Follow pattern in `test/test_voice_input_node.py`.
