# control — Current Session Handoff

Use this file as the first context document at the start of a new session. It is
not intended to replace `README.md`; keep full usage details there. This file
should answer: what is built, what likely comes next, and what loose issues need
attention.

## Snapshot

**Branch:** `main`

This repo is the ROS2 control package and CLI for robot movement, launch/process
management, map operations, configuration, scripts, and intent publishing.

## What Is Built

- CLI with REPL and non-interactive modes (`SimpleCLI` → `CommandDispatcher.dispatch_text`).
- Command dispatcher with two routing paths:
  - **Behavior path**: behavior commands (`scene describe`, `scene objects`, `intent stop`, etc.)
    publish JSON to `/intent` via `IntentPublisher`. Query intents wait up to 5s for reply on
    `/announcement` and print the result in the CLI.
  - **Direct path**: all other commands call `RobotController` methods synchronously.
- `RobotController` orchestration layer.
- ROS2 API wrappers: movement, calibration, process, intent publishing.
- Launch management through configured templates.
- Map save/list/serialize commands.
- `BehaviorManagerNode`: subscribes to `/intent` and `/oak/detections`, routes to domain handlers.
  Caches latest `Detection2DArray` in `latest_detections` for `PerceptionBehavior`.
- `MotionBehavior`: handles `stop`, `explore`, `drive_square`, `turn_right`, `turn_left`, `get_status`.
- `PerceptionBehavior`: handles `describe_scene` (async service call), `list_objects` (cached detections).
- `IntentParser`: pure Python JSON→Intent parser.
- `describe_scene_stub` node for smoke testing without vision hardware.
- Voice pipeline extracted to sibling package `robot_voice` (see `src/robot_voice/`).
  `voice_input_node.py` is the ROS2 adapter in control that imports from `robot_voice`.
- Voice intent mapping: 8 single-word commands — stop, right, left, explore, describe, objects, status, help.
- Wake word: "alexa". Threshold 0.7, wake_hits 3, cooldown 1.5s.
- `audio_feedback.py` (in robot_voice): beep via aplay, 20% amplitude.
- Launch files:
  - `launch/robot.launch.py` — robot nodes. Args: `voice`, `behavior`, `oak`.
    `oak:=true` launches `oak_roboflow_ros_node` (lifecycle) instead of `describe_scene_stub`.
  - `launch/remote.launch.py` — remote/dev nodes.
- Feature files:
  - `F01`–`F03`, `F13`–`F15`: done
  - `F16` list-detected-objects: in progress

## Known Issues / Pending

- **Empty STT turns**: voice turns returning empty. Debug log in `voice_input_node` shows
  `floor`/`cutoff`/`command_started`/`raw_text`. Next: observe on hardware.
- **Wake re-trigger**: cooldown fix unconfirmed on hardware.
- **`scene describe` with real oak**: `oak_roboflow_ros` has no `/describe_scene` service.
  With `oak:=true`, `scene describe` silently no-ops. Need to implement service in oak_roboflow_ros
  or wire describe_scene through `/oak/detections` same as `list_objects`.

## Likely Next Steps

1. Implement `/describe_scene` service in `oak_roboflow_ros` for real camera.
2. Test `scene objects` with real oak hardware (`bl control robot.launch.py oak:=true`).
3. Observe empty-turn voice debug log on hardware.
4. Split `RobotController` into smaller modules.

## Quick Commands

```bash
# Tests
python3 -m pytest test/ -v

# CLI
ros2 run control run

# Launch robot (stub)
bl control robot.launch.py

# Launch robot with real oak camera
bl control robot.launch.py oak:=true

# Launch full stack
bl control robot.launch.py oak:=true voice:=true
```
