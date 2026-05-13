# Tasks for Feature F14

## T01 — Provide a pasteable tuned parameter block
**Status**: done
**Description**: Add one obvious place in the production voice code where the
latest winning values from `~/tune` can be copied by hand. Keep the shape close
to tune's `active.yaml`: top-level capture/playback cards, `stream_settings`,
and `sox_chain`. The block must include wake word, wake threshold, wake-hit
count, live filter flag, highpass/lowpass cutoffs, Vosk model, grammar, and
capture/playback cards. Dynamic YAML loading is optional and should only be a
comparison/testing convenience; the main requirement is that it is easy to see
and verify the parameters currently compiled into `control`.

## T02 — Build ROS-free runtime shell
**Status**: done
**Description**: Create `control.voice.runtime` with no `rclpy` imports. The
runtime should expose a typed turn/result object and a simple smoke-test entry
point, but it should not publish ROS topics or move the robot. Test that the
module imports without ROS installed.

## T03 — Move tuned audio stream handling into runtime
**Status**: done
**Description**: Implement the production voice algorithms directly in the shared
runtime: `arecord` stereo capture, stereo-to-mono conversion, DC offset removal,
optional live highpass/lowpass filtering, wake detection, command capture, and
Vosk transcription. These algorithms may be fixed in `control`; they do not need
to track every experimental algorithm in `tune`. What must stay aligned is the
parameter surface from the winning tune run. Test audio helper functions with
synthetic chunks and fake wake and STT models.

## T04 — Refactor voice_input_node into ROS adapter
**Status**: done
**Description**: Make `dome_voice/voice_input_node.py` call the shared runtime for
voice turns, map transcripts with `IntentMapper`, publish `/voice/state`, publish
mapped JSON intents on `/intent`, and publish an `/announcement` failure message
when mapping fails. Test with a fake runtime result.

## T05 — Align tuned motion phrases with intent mapping
**Status**: done
**Description**: Update or explicitly pair this feature with an intent-mapper
change so `go forward`, `go backward`, `turn left`, `turn right`, and `stop`
produce the expected normalized movement/stop intents. Test every tuned grammar
phrase.

## T06 — Run Pi hardware smoke test
**Status**: done
**Description**: On the Pi with the ReSpeaker HAT and installed voice models,
run `python3 -m control.voice.runtime --trials 5`. Confirm wake hits,
transcripts, empty count, and latency are plausible with the pasted
`TUNED_VOICE_PARAMETERS`. This is a manual hardware check.
