# Feature description for feature F04
## F04 — Voice input node (Porcupine + Rhino)
**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Extend the existing `voice_input_node` from a hardcoded
`describe_scene` stub into a full openWakeWord + Vosk pipeline. On hearing
"Hey Jarvis", Vosk transcribes the utterance and a keyword matcher maps it to
a structured intent JSON published on `/intent`. The voice state machine
(IDLE → LISTENING → PROCESSING → SPEAKING → IDLE) is implemented and its state
published on `/voice/state`. Unmatched utterances trigger an "I didn't catch that"
announcement. See `02-doc/control-architecture.md` Phase 3 for full spec.

## How to Demo
**Setup**: ReSpeaker HAT on Pi, `openwakeword` and `vosk` installed in dome-voice
venv, `vosk-model-small-en-us` downloaded, `VOSK_MODEL_PATH` set, ROS2 environment
sourced, `behavior_manager_node` running.

**Steps**:
1. `ros2 run control voice_input`
2. Say "Jarvis"
3. Say a recognized command, e.g. "what do you see?"
4. `ros2 topic echo /intent`
5. Say "Jarvis" then an unrecognized phrase

**Expected output**: step 4 shows `{"name": "describe_scene", "source": "voice",
"slots": {}}`. Step 5 produces an `/announcement` with "I didn't catch that".
