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

## Runtime tuning notes

Current useful settings for ReSpeaker/Seeed HAT testing:

```bash
export PIPER_BIN=/home/pitosalas/ros2_ws/src/dome_control/bin/piper/piper
export PIPER_MODEL_PATH=/home/pitosalas/ros2_ws/src/dome_control/piper_model/en_US-lessac-medium.onnx
export SPEECH_ALSA_DEVICE=plughw:0,0
export SPEECH_TMP_DIR=/dev/shm
export SPEECH_GAIN=0.18
export PIPER_LENGTH_SCALE=1.55
```

Notes:
- `SPEECH_TMP_DIR=/dev/shm` keeps generated WAV files in RAM instead of
  writing them to the microSD card.
- `SPEECH_GAIN` attenuates Piper playback only; it does not change microphone
  gain, wake-word capture, or Vosk transcription.
- `PIPER_LENGTH_SCALE` controls Piper speed. Larger values are slower; smaller
  values are faster. `1.55` was a better initial value than Piper's default.
- Avoid changing capture-side ALSA controls (`PGA`, `AGC`, `Mic2*`, capture
  muxes) while tuning TTS output, because those will affect wake word and STT.
- If speech is still too loud, try `SPEECH_GAIN=0.12` or `0.08`.
- If speech is too quiet, try `SPEECH_GAIN=0.25`.
- If speech is still too fast, try `PIPER_LENGTH_SCALE=1.75`.
- If speech is too slow, try `PIPER_LENGTH_SCALE=1.35`.
- Future improvement: keep the gain/rate defaults in a config file or launch
  file instead of requiring shell exports.
