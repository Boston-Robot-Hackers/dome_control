# control — Current Session Handoff

Use this file as the first context document at the start of a new session. It is
not intended to replace `README.md`; keep full usage details there. This file
should answer: what is built, what likely comes next, and what loose issues need
attention.

## Snapshot

**Branch:** `main`

This repo is the ROS2 control package and CLI for robot movement, launch/process
management, map operations, configuration, scripts, and intent publishing.

The repository has been migrated to the numbered process/documentation layout:
- `01-literate/` — generated literate docs
- `02-doc/` — project docs, `spec.md`, `current.md`, `notes.md`
- `03-features/` — feature records
- `04-tasks/` — task records
- `05-issues/` — loose issues not yet converted to features

## What Is Built

- CLI with REPL and non-interactive modes (`SimpleCLI` → `CommandDispatcher.dispatch_text`).
- Command dispatcher with two routing paths:
  - **Behavior path**: behavior commands (`scene describe`, `intent stop`, etc.) publish
    JSON to `/intent` via `IntentPublisher`. Listed in `help commands`.
  - **Direct path**: all other commands call `RobotController` methods synchronously.
- `RobotController` orchestration layer.
- ROS2 API wrappers: movement, calibration, process, intent publishing.
- Launch management through configured templates.
- Map save/list/serialize commands.
- `BehaviorManagerNode`: subscribes to `/intent`, routes to domain behavior handlers
  (`MotionBehavior`, `PerceptionBehavior`). `get_help` intent handled inline (speaks command list).
- `MotionBehavior`: handles `stop`, `explore`, `drive_square`, `turn_right`, `turn_left`, `get_status` intents.
- `PerceptionBehavior`: handles `describe_scene` (async ROS2 service call → `/announcement`).
- `IntentParser`: pure Python JSON→Intent parser.
- `describe_scene_stub` node for smoke testing without vision hardware.
- Shared tuned voice runtime in `control/voice/runtime.py` with thin `voice_input` adapter.
- Voice intent mapping: 7 single-word commands — stop, right, left, explore, describe, status, help.
- Wake word: "alexa". Threshold 0.7, wake_hits 3, cooldown 1.5s (flushes OWW model state).
- `audio_feedback.py`: beep via aplay (same ALSA device as Piper), 20% amplitude.
- Colcon-compatible launch files:
  - `launch/robot.launch.py` — on-robot nodes, with `voice` and `behavior` launch args
  - `launch/remote.launch.py` — remote/dev nodes, with `voice` and `behavior` launch args
  - Both registered in `launch_templates` in `control-config.yaml` as `robot` and `remote`.
- Existing feature files:
  - `F01` intent publishing: done
  - `F02` structural code cleanup: done
  - `F03` semantic behavior pipeline MVP: done
  - `F13` multi-machine deployment configurations: done
  - `F14` shared tuned voice runtime: done
  - `F15` unified intent architecture: done

## Known Issues / Pending

- **Empty STT turns**: All voice turns returning empty (no transcription). Debug log added to
  voice_input_node to show `floor`/`cutoff`/`command_started`/`raw_text` on each empty turn.
  Next: observe log output to distinguish mic level problems from grammar mismatch.
- **Wake re-trigger**: OWW model cooldown now feeds chunks to model to flush sliding window.
  Threshold 0.7 + wake_hits 3. Not yet confirmed fully fixed on hardware.
- `turn_right`, `turn_left` now wired to `turn_clockwise(90)` / `turn_counterclockwise(90)`.
  `cmd_vel_helper` blocks behavior_manager callback thread during turn (open-loop, no odom).
- `get_status` speaks linear/angular speed via announcement bus.

## Likely Next Steps

1. **Observe empty-turn debug log** — run robot, say "alexa stop", check log for
   `floor`/`cutoff`/`command_started`/`raw_text`. If `command_started=False`, mic too quiet
   or silence_margin too strict. If `command_started=True` and `raw_text=''`, Vosk grammar mismatch.

2. **Replace describe_scene_stub with real oak_roboflow query path.**

3. **Split `RobotController` into smaller modules.**

## Quick Commands

Run tests:

```bash
python3 -m pytest test/ --ignore=test/test_voice_runtime.py -v
```

Run the CLI:

```bash
ros2 run control run
```

Launch on robot:

```bash
bl control robot.launch.py
```

Voice runtime smoke test:

```bash
python3 -m control.voice.runtime --trials 5
```
