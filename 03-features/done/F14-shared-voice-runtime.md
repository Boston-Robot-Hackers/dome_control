# Feature description for feature F14
## F14 — Shared tuned voice runtime with thin ROS wrapper
**Priority**: High
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Replace the current ROS-heavy voice input implementation with a
small shared runtime in `dome_voice` that owns the Raspberry Pi audio loop:
microphone capture, live filtering, wake-word detection, command capture, and
Vosk transcription. The runtime must be usable without ROS so audio tuning and
hardware validation can happen directly on the Pi. The ROS node should become a
thin adapter that receives transcripts from the runtime, maps them to intents,
and publishes `/intent`, `/voice/state`, and `/announcement`.

## Background

The tuned `tune` harness and `demo_listen.py` now have better runtime behavior
than `dome_voice.voice_input_node`:

- wake word: `alexa`
- wake threshold: `0.3`
- wake hits: `1`
- live filter: enabled
- highpass: `120 Hz`
- lowpass: `4000 Hz`
- Vosk model: `small`
- Vosk grammar: `go forward`, `go backward`, `turn left`, `turn right`, `stop`

The current `control` voice stack still uses older defaults:

- wake word defaults to Hey Jarvis
- wake threshold is hardcoded at `0.5`
- PyAudio mono capture is used directly
- tuned stereo-to-mono, DC removal, and highpass/lowpass filtering are missing
- Vosk grammar comes from `intent_mapper.VOSK_COMMANDS`, which does not include
  the recently tested robot motion phrases
- `voice_input_node.py` owns both audio control and ROS publishing, making it
  harder to test the Pi audio path without ROS

## Target Architecture

Keep the action boundary at `/intent`. The audio runtime should not directly move
the robot. It should produce recognized command text and metadata. ROS-dependent
code should translate that into topics.

```
dome_voice.runtime             # no ROS imports
  arecord / audio input
  live filter
  openWakeWord
  command capture
  Vosk grammar transcription
  -> VoiceTurn(text, raw_text, timings, scores)

dome_voice.voice_input_node         # ROS adapter only
  runtime.next_turn()
  IntentMapper.map_intent(text)
  publish /voice/state
  publish /intent
  publish /announcement on failure
```

## Non-ROS Runtime Requirements

Add a pure-Python module, likely `dome_voice/runtime.py`, with no `rclpy`
imports. It should be able to run on the Pi from a plain Python script or test
command.

Responsibilities:

1. Load tuned defaults from a small config source.
2. Open the microphone stream using the same approach proven in `tune`:
   `arecord`, 16 kHz, 16-bit, stereo input, converted to mono.
3. Remove DC offset from each chunk.
4. Apply live highpass/lowpass filtering when enabled.
5. Load openWakeWord and detect the configured wake word.
6. Require configurable consecutive wake hits.
7. Capture the post-wake command using adaptive silence detection.
8. Transcribe with Vosk using the configured grammar.
9. Return a structured result object with transcript, raw transcript, wake score,
   timing, empty flag, and useful debug metadata.
10. Provide a standalone entry point or script for Pi-only smoke testing.

The runtime should preserve command-line overrides for threshold, wake hits,
grammar, live filter, highpass, lowpass, and model paths.

## ROS Wrapper Requirements

Refactor `dome_voice/voice_input_node.py` so it is mostly ROS glue:

1. Publish `IDLE`, `LISTENING`, `PROCESSING`, and `SPEAKING` states.
2. Call the shared runtime for each voice turn.
3. Pass the recognized text to `IntentMapper`.
4. Publish mapped intents to `/intent` as JSON.
5. Publish "I didn't catch that" to `/announcement` when mapping fails.
6. Avoid direct microphone, wake-word, or Vosk implementation details in the node.

The ROS wrapper may still handle beeps, but robot-side spoken feedback should
prefer `/announcement` where practical so deployment can place audio output on
the robot and voice input on another machine.

## Configuration

Support the tuned defaults from the `tune` project. Initial values:

```yaml
stream_settings:
  wake_word: alexa
  threshold: 0.3
  wake_hits: 1
  live_filter: true
  highpass: 120
  lowpass: 4000
  vosk_model: small
  grammar:
    - go forward
    - go backward
    - turn left
    - turn right
    - stop
```

The config mechanism can be either:

- read `.tune/active.yaml` when available, or
- copy the same schema into `control` config and keep the loader isolated

Do not make ROS parameters the only source of truth for the Pi-only runtime.
The non-ROS smoke test must be able to use the same values.

## Intent Mapping Follow-up

The current `IntentMapper` does not map the tuned motion phrases. This feature
should either include or explicitly pair with a mapper update so these phrases
produce useful intents:

| Transcript | Expected intent |
|------------|-----------------|
| `go forward` | movement or navigation intent for forward motion |
| `go backward` | movement or navigation intent for backward motion |
| `turn left` | turn intent |
| `turn right` | turn intent |
| `stop` | `stop` |

Keep the precise intent names aligned with the behavior manager and existing
command vocabulary before implementation.

## Tests

Required tests:

1. Runtime config loader uses tuned defaults and allows overrides.
2. Runtime module imports without ROS installed.
3. Audio chunk conversion removes DC offset and produces mono samples.
4. Live filter can be enabled and disabled.
5. Wake detection honors threshold and wake-hit count using a fake model.
6. Command capture returns empty text on timeout and transcript text on speech.
7. ROS node test proves the node publishes `/intent` for a fake runtime transcript.
8. ROS node test proves failed mapping publishes an announcement.

Hardware smoke test:

```bash
python3 -m control.voice.runtime --trials 5
```

Expected Pi-only output should show wake hit count, empty count, match count if a
phrase is supplied, and median latency, matching the `tune streamtest prompted`
style.

## How to Demo

**Setup**: Raspberry Pi with ReSpeaker HAT, `openwakeword`, `vosk`, Vosk small
English model, and the tuned microphone placement from the latest `tune` tests.

**Steps**:
1. Run the non-ROS runtime smoke test on the Pi.
2. Say `alexa go forward` for several trials.
3. Confirm the runtime reports wake hits, transcripts, and latency without ROS.
4. Start ROS nodes: `voice_input`, `behavior_manager`, and any action consumer.
5. Say `alexa go forward`.
6. Echo `/intent`.

**Expected output**: The standalone runtime recognizes commands using the tuned
settings. The ROS node publishes a valid intent JSON for the recognized command,
with audio implementation details isolated outside the ROS wrapper.
