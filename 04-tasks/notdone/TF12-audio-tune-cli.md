# Tasks for Feature F12 — Audio tuning CLI test harness

Task file name: `TF12-audio-tune-cli.md`
**Code location:** `~/tune/` — standalone, outside ros2_ws. Run: `python3 ~/tune/tune.py`

## T01 — Project scaffold and CLI entry point
**Status**: done
**Description**: Create `tune/` directory with `tune.py` entry point using `argparse` or `click`. Subcommand skeleton: `config`, `record`, `play`, `sweep`, `score`, `snr`, `ab`, `profile`, `results`, `devices`. No logic yet, just subcommand dispatch and `--help`. Add `requirements.txt` (PyYAML, click or argparse). Verify `python tune.py --help` lists all subcommands.

## T02 — Device detection (`tune devices`)
**Status**: done
**Description**: Parse `arecord -l` and `aplay -l` output to list available cards with index and name. Print table of capture and playback devices. Read `config.yaml` (or default) and show which card is assigned to `capture_card` and `playback_card`. Test: run on Pi, confirm ReSpeaker appears with correct card index.

## T03 — Config YAML schema and apply/save/list
**Status**: done
**Description**: Define YAML schema with: `capture_card`, `playback_card`, ALSA controls dict (control name → value), SoX chain list, noise suppression flag/engine, KWS engine name. Implement `tune config apply <preset>` (runs `amixer sset` for each control), `tune config save <preset>` (dumps current `amixer scontents` to YAML), `tune config list` (shows presets in `~/.tune/presets/`). Include baseline preset matching current recommended state from `seeedtuning.md`. Test: apply baseline, verify `amixer` controls match expected values.

## T04 — Record command with stage timing
**Status**: done
**Description**: Implement `tune record <name> [--duration 5]`. Captures stereo WAV to `~/tmp/<name>-raw.wav` via `arecord hw:<capture_card>,0`. Times `capture` stage (subprocess wall time). Saves timing to sidecar JSON `~/tmp/<name>-meta.json`. Test: record 3 s clip, verify WAV exists, is stereo 16 kHz 16-bit, meta JSON has `capture_ms`.

## T05 — SoX filter stage with timing
**Status**: done
**Description**: Implement filter stage: read SoX chain from config, run `sox` on raw WAV to produce `<name>-clean.wav`. Time `filter` stage. Parameters: remix mode (left/right/both), highpass Hz, lowpass Hz, normalization headroom dB. Save `filter_ms` to meta JSON. Test: process known WAV, verify output mono, correct sample rate, meta updated.

## T06 — SNR estimation (`tune snr`)
**Status**: done
**Description**: Estimate SNR from a recording: split WAV into first 0.5 s (assumed silence/lead-in) vs detected voice segment (peak RMS window). Report dBFS for each and SNR difference. Use `sox` stats or `librosa`/`soundfile` in Python. Test: run on a recording with known voice, verify silence floor < voice level.

## T07 — Noise suppression stage
**Status**: not done
**Description**: Add optional noise suppression step between filter and KWS. Support: `none`, `rnnoise` (via `rnnoise_demo` CLI or Python binding), `webrtc` (via `webrtcvad` or `py-webrtc-noise-gain`). Time `noise_suppress` stage. If engine not installed, warn and skip. Test: run RNNoise on noisy clip, verify output WAV, `noise_suppress_ms` in meta.

## T08 — KWS/wake-word scoring (`tune score`)
**Status**: not done
**Description**: Implement `tune score <name> --engine <engine>`. Supported engines: `openwakeword`, `porcupine`, `vosk`. Run engine on processed WAV file (offline, not streaming). Count detections, report hit rate. Time `kws` stage. Compute `e2e_ms = capture_ms + filter_ms + noise_suppress_ms + kws_ms`. Save all to meta JSON. Test: run openWakeWord on WAV containing wake word, expect ≥1 detection.

## T09 — Per-stage latency profile (`tune profile`)
**Status**: not done
**Description**: Read meta JSON for a named recording, print ASCII bar chart of per-stage timing: `capture`, `filter`, `noise_suppress`, `vad`, `kws`, `e2e`. Highlight slowest stage. Test: generate profile output for a scored recording, verify all stage columns present and e2e = sum of stages.

## T10 — Sweep mode (`tune sweep`)
**Status**: not done
**Description**: Implement `tune sweep <param> <start> <stop> <step>`. Supported params: `pga`, `hpf`, `highpass`, `lowpass`. For each value: apply config, record test clip, run SNR + score, log to results CSV. Print progress table during sweep. Test: sweep PGA 40–60 in steps of 10, verify results CSV has 3 rows with correct PGA values.

## T11 — Results log and table (`tune results`)
**Status**: not done
**Description**: Append every `record`/`sweep`/`score` run to `~/.tune/results.csv`. Columns: timestamp, preset, capture_card, playback_card, PGA, HPF, highpass_hz, lowpass_hz, noise_suppress, kws_engine, SNR_dB, hit_rate, false_pos_rate, capture_ms, filter_ms, noise_suppress_ms, kws_ms, e2e_ms, notes. `tune results` prints table sorted by e2e_ms ascending, with SNR and hit_rate columns highlighted. Test: run two sweeps, verify CSV row count and column completeness.

## T12 — A/B playback comparison (`tune ab`)
**Status**: not done
**Description**: Implement `tune ab <name1> <name2>`. Plays `<name1>-clean.wav` then `<name2>-clean.wav` via `aplay plughw:<playback_card>,0` with 1 s gap. Prompts user for preference (1/2/tie) and saves to results log. Test: run on two differently-filtered versions of same raw recording, verify playback completes and preference logged.

## T13 — Dual-board smoke test
**Status**: not done
**Description**: Verify full pipeline works when `capture_card != playback_card`. Set config with ReSpeaker as capture (card 0) and a second device as playback (e.g. USB audio or Pi headphone jack). Run `tune record`, `tune play`, verify no cross-device errors. Document in `seeedtuning.md` which card indices correspond to which hardware in the test setup.
