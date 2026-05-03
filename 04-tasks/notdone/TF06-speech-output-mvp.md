# Tasks for Feature F06

## T01 — Add `speech_output_node` shell and ROS2 wiring
**Status**: done
**Description**: Create node entrypoint, subscribe to `/announcement`, and add
basic lifecycle/logging.

## T02 — Integrate Piper synthesis path
**Status**: done
**Description**: Convert announcement text to WAV via Piper CLI/library, with
configurable model path.

## T03 — Integrate ALSA playback path
**Status**: done
**Description**: Play synthesized WAV through configured audio output device.

## T04 — Add runtime configuration
**Status**: done
**Description**: Add env vars/params for Piper binary/model and ALSA device
selection.

## T05 — Add smoke tests
**Status**: done
**Description**: Add minimal tests/mocks for node flow and synthesis/playback
invocation behavior.
