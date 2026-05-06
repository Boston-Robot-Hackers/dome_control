# Feature description for feature F12
Feature file name must be `F12-audio-tune-cli.md` where `12` matches the feature number.
## F12 — Audio tuning CLI test harness

**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes (T01–T05)
**Test Passing:** yes
**Location:** `~/tune/` (standalone, outside ros2_ws)
**Description**: CLI tool (`tune`) for systematically exploring ReSpeaker 2-Mics HAT V2.0 configuration space to find optimal settings for far-field robot voice commands. Covers ALSA hardware parameters, SoX software filtering, noise suppression, and KWS/wake-word engine selection. Results logged per run for cross-session comparison.

**Parameter dimensions:**
- ALSA: `PGA` level (40–70%), `ADC HPF Cut-off` enum, input mode (single-ended vs differential), mic routing (left/right/both)
- SoX: highpass cutoff, lowpass cutoff, normalization headroom
- Noise suppression stage: none / RNNoise / WebRTC NS
- KWS/wake-word engine: Porcupine, openWakeWord, Vosk KWS, Whisper tiny

**Architecture:**
- Pure Python CLI, no ROS2 dependency — lives at `~/tune/`, run with `python3 ~/tune/tune.py`
- Config stored as YAML (ALSA controls + SoX chain); presets in `~/tune/presets/`; active config at `~/.tune/active.yaml`
- Results log: CSV or SQLite, one row per run (timestamp, preset, all params, scores)
- Test corpus: fixed raw stereo WAV files reused across config runs to isolate software variables
- **Dual-board support**: capture board (mic input) and playback board (speech output) configured independently; may be same card or different cards. Config YAML has separate `capture_card` and `playback_card` keys. Allows e.g. ReSpeaker for mic input + USB DAC or Pi headphone jack for TTS output.

**Stage instrumentation:**
Pipeline broken into named stages; each stage timed independently and logged per run:
- `capture` — `arecord` to raw WAV (hardware latency + buffer fill time)
- `filter` — SoX processing (highpass, lowpass, remix, normalize)
- `noise_suppress` — RNNoise / WebRTC NS (if enabled)
- `vad` — voice activity detection (time to detect speech start/end)
- `kws` — keyword spotting / wake word engine (time from audio chunk to detection callback)
- `e2e` — end-to-end: utterance end → KWS callback (sum of relevant stages)

Stage timing logged as columns in results CSV. `tune profile <name>` command shows per-stage breakdown for a run. Goal: identify which stage dominates latency budget so optimization effort is targeted.

**Scoring metrics:**
- SNR estimate (dBFS voice vs silence floor)
- KWS hit rate (N utterances of each command, count detections)
- False positive rate (silence/motor-noise segment)
- Per-stage latency (ms) + end-to-end latency
- Manual subjective flag per run

## How to Demo

**Setup**:
- ReSpeaker HAT connected, `arecord -l` shows `seeed2micvoicec` as card 0
- `~/tmp` directory exists
- Test corpus recorded: commands at 1 m and 2 m, silence segment, wake word at both distances

**Steps**:
1. `tune config list` — show available presets
2. `tune config apply baseline` — apply known-good starting config
3. `tune record go-1m --duration 3` — record test utterance
4. `tune snr go-1m` — show SNR estimate
5. `tune sweep pga 40 70 5` — sweep PGA values, auto-record and score each
6. `tune results` — show results table sorted by SNR
7. `tune ab baseline best-pga` — back-to-back playback comparison
8. `tune score go-1m --engine openwakeword` — run wake word engine, report hit rate + latency

**Expected output**:
- `tune results` shows table with columns: preset, PGA, HPF, highpass, SNR, hit_rate, capture_ms, filter_ms, kws_ms, e2e_ms
- `tune profile <run-id>` shows per-stage breakdown bar chart (ASCII) to spot bottleneck
- Best config row identifiable by highest SNR + hit rate + lowest e2e latency
- Named preset saveable with `tune config save <name>` for use in production pipeline
- Dual-board config verified with `tune devices` showing detected capture and playback cards
