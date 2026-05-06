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
  (`MotionBehavior`, `PerceptionBehavior`). Handler list is extensible.
- `MotionBehavior`: handles `stop`, `explore`, `drive_square` intents.
- `PerceptionBehavior`: handles `describe_scene` (async ROS2 service call → `/announcement`).
- `IntentParser` (renamed from `BehaviorManager`): pure Python JSON→Intent parser.
- `describe_scene_stub` node for smoke testing without vision hardware.
- Shared tuned voice runtime in `control/voice/runtime.py` with thin `voice_input` adapter.
- Voice intent mapping covers tuned motion phrases from `~/tune`.
- Colcon-compatible launch files:
  - `launch/robot.launch.py` — on-robot nodes (behavior_manager, speech_output, voice_input)
  - `launch/remote.launch.py` — remote/dev nodes (describe_scene_stub)
  - Both registered in `launch_templates` in `control-config.yaml` as `robot` and `remote`.
- Existing feature files:
  - `F01` intent publishing: done
  - `F02` structural code cleanup: done
  - `F03` semantic behavior pipeline MVP: done
  - `F14` shared tuned voice runtime: code done; Pi hardware smoke test pending
  - `F15` unified intent architecture: T01–T07 done; T08 (smoke test) pending

## Likely Next Steps

1. **T08: Smoke test F15 end-to-end with ROS2 running.**
   CLI `stop` → `/intent` → behavior_manager → RobotController. Verify with
   `ros2 topic echo /intent` and `ros2 topic echo /announcement`.

2. **Implement `speak` CLI command.**
   Direct path: `speak <text>` → `RobotController.speak_text` → publishes to `/announcement`.
   Robot side needs only `speech_output_node` — no `BehaviorManagerNode` required.

3. **Replace describe_scene_stub with real oak_roboflow query path.**
   Feature: no feature yet. Provide a real `/describe_scene` service backed by
   `/targets/confirmed`, then point `PerceptionBehavior` at that.

4. **Run F14 voice runtime hardware smoke test on the Pi.**
   Feature: `F14`. Command: `python3 -m control.voice.runtime --trials 5` on Pi with
   ReSpeaker/openWakeWord/Vosk installed.

5. **Split `RobotController` into smaller modules.**
   Feature: no feature yet. `robot_controller.py` is still large.

6. **Add health checks for launched processes.**
   Feature: no feature yet.

## Loose Issues Not Yet Converted To Features

- `robot_controller.py` is large and should be split.
- Some debug print statements may remain in controller/API code.
- Process health checks are not implemented.
- Map operations should validate map file existence more defensively.
- F14 voice runtime still needs Pi hardware smoke testing.
- F15/T08 smoke test still pending (needs ROS2 environment).

## Quick Commands

Run tests:

```bash
python3 -m pytest test/ -v --ignore=test/__init__.py
```

Run the CLI:

```bash
ros2 run control run
```

Launch on robot:

```bash
ros2 launch control robot.launch.py
```

Launch on remote machine:

```bash
ros2 launch control remote.launch.py
```

Run voice runtime smoke test:

```bash
python3 -m control.voice.runtime --trials 5
```
