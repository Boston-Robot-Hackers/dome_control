---
version: "1.0"
generated: "2026-05-04"
---

# System Commands

`system_commands.py` defines the command registry entries for configuration management, scripted movement patterns, and system-level process inspection. It bundles four conceptually distinct groups: `config`, `script`, `system`, and implicitly exposes `map` operations via the navigation group.

## Groups Covered

### config

```
config.set   name value     → RobotController.set_variable
config.get   name           → RobotController.get_variable
config.list                 → RobotController.get_all_variables
```

Exposes `ConfigManager` through the CLI. `config.list` filters out `launch_templates` from the output (it's too verbose for a terminal display).

### script

```
script.list                 → lists available scripts
script.square       meters  → CalibrationApi.run_square_pattern
script.rotate_stress        → CalibrationApi.run_rotate_stress
script.circle_stress diameter → CalibrationApi.run_circle_stress
```

These are the only commands that directly invoke multi-step, long-running motion sequences. They block the CLI until the pattern completes or the user interrupts with Ctrl+C.

### system

```
system.topics    → list active /topics via MovementApi.get_topic_names_and_types
system.ps        → list all ROS-related OS processes (ps aux filtered)
system.kill pid  → kill process by PID (group kill if PID == PGID)
system.launches  → list ros2 launch parent processes (filtered from ps)
```

`system.kill` is noteworthy: `RobotController.kill_ros_process` first checks whether the target PID is a process group leader by comparing PID == PGID. If it is, it sends `SIGTERM` to the whole process group (`kill -TERM -PID`). This is the correct way to shut down a `ros2 launch` invocation — killing just the launcher process leaves all its children orphaned.

## Observations

- `system.topics` uses `self.movement.get_topic_names_and_types()`, which creates a `MovementApi` node on first call. This has the side effect of initialising a full ROS2 subscriber set just to list topics. A lightweight dedicated node or `ros2 topic list` subprocess call would be cleaner.
- `script.rotate_stress` has no timeout parameter — it runs until Ctrl+C. For remote operation this is hazardous; adding an optional `--max-seconds` parameter would be safer.
- `config.set` and `config.get` are in `system_commands.py` but the `config` group name is distinct from `system`. Future refactoring could split config into its own file.
