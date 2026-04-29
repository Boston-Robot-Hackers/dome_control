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
- Existing feature files:
  - `F01` intent publishing: done
  - `F02` structural code cleanup: done

## Likely Next Steps

1. **Create a feature for the semantic behavior pipeline.**
   Feature: no feature yet. This should probably track the next cross-repo step from
   `oak_roboflow/02-doc/implementation-plan.md`: CLI command such as
   `scene describe` publishes `/intent`, a behavior manager receives it, calls a
   describe-scene service, and reports a summary.

2. **Split `RobotController` into smaller modules.**
   Feature: no feature yet. `robot_controller.py` is still large and should be split
   before more behavior is added.

3. **Clean up debug output and exception handling.**
   Feature: no feature yet. Convert debug prints to logging where still present and
   tighten overly broad exception handling.

4. **Add health checks for launched processes.**
   Feature: no feature yet. Launch commands currently manage process lifecycle; the
   next useful improvement is active health/status reporting.

5. **Keep `02-doc/current.md` updated after meaningful sessions.**
   Feature: no feature needed. When a likely next step has a feature number, include
   that feature number in this list.

## Loose Issues Not Yet Converted To Features

- `robot_controller.py` is large and should be split.
- Some debug print statements may remain in controller/API code.
- Process health checks are not implemented.
- Map operations should validate map file existence more defensively.

## Quick Commands

Run tests:

```bash
python3 -m pytest test/ -v --ignore=test/__init__.py
```

Run the CLI:

```bash
ros2 run control run
```
