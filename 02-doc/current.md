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

- CLI with REPL and non-interactive modes.
- Command dispatcher and command groups for movement, launch, map, config, script,
  system, and intent commands.
- `RobotController` orchestration layer.
- ROS2 API wrappers including movement, calibration, process, and intent publishing.
- Launch management through configured templates.
- Map save/list/serialize commands.
- Intent publishing to `/intent` using `std_msgs/String` JSON.
- Semantic `scene describe` and `scene count <object_type>` CLI aliases.
- `behavior_manager` node that receives `/intent`, calls `/describe_scene`,
  and publishes `/announcement` JSON.
- Temporary `describe_scene_stub` node for smoke testing.
- Shared tuned voice runtime in `control/voice/runtime.py` with a thin
  `voice_input` ROS adapter.
- Voice intent mapping now covers the tuned motion phrases from `~/tune`
  and keeps the runtime parameter block easy to paste from the latest run.
- Existing feature files:
  - `F01` intent publishing: done
  - `F02` structural code cleanup: done
  - `F03` semantic behavior pipeline MVP: done
  - `F14` shared tuned voice runtime: code and tests are in place; Pi hardware
    smoke test still pending

## Likely Next Steps

1. **Replace the describe-scene stub with the real oak_roboflow query path.**
   Feature: no feature yet. The next cross-repo step is to provide a real
   `/describe_scene` service backed by latest `/targets/confirmed`, then point
   `behavior_manager` at that instead of `describe_scene_stub`.

2. **Run F14 voice runtime hardware smoke test on the Pi.**
   Feature: `F14`. Shared tuned voice runtime code and tests are in place, with
   pasted `TUNED_VOICE_PARAMETERS` in `control/voice/runtime.py`. The remaining
   check is `python3 -m control.voice.runtime --trials 5` on the Pi with
   ReSpeaker/openWakeWord/Vosk installed.

3. **Split `RobotController` into smaller modules.**
   Feature: no feature yet. `robot_controller.py` is still large and should be split
   before more behavior is added.

4. **Clean up debug output and exception handling.**
   Feature: no feature yet. Convert debug prints to logging where still present and
   tighten overly broad exception handling.

5. **Add health checks for launched processes.**
   Feature: no feature yet. Launch commands currently manage process lifecycle; the
   next useful improvement is active health/status reporting.

6. **Keep `02-doc/current.md` updated after meaningful sessions.**
   Feature: no feature needed. When a likely next step has a feature number, include
   that feature number in this list.

## Loose Issues Not Yet Converted To Features

- `robot_controller.py` is large and should be split.
- Some debug print statements may remain in controller/API code.
- Process health checks are not implemented.
- Map operations should validate map file existence more defensively.
- F14 voice runtime still needs Pi hardware smoke testing.

## Quick Commands

Run tests:

```bash
python3 -m pytest test/ -v --ignore=test/__init__.py
```

Run the CLI:

```bash
ros2 run control run
```

Run the voice runtime smoke test:

```bash
python3 -m control.voice.runtime --trials 5
```
