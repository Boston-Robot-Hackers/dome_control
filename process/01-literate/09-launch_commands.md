---
version: "1.0"
generated: "2026-05-04"
---

# Launch Commands

`launch_commands.py` defines the command registry entries for managing ROS2 launch processes. These commands expose `ProcessApi`'s lifecycle management through the CLI.

## The Registry

```python
"launch.list":  CommandDef("launch_list",  [], ...)
"launch.info":  CommandDef("launch_info",  [ParameterDef("launch_type", str, True, ...)], ...)
"launch.start": CommandDef("launch_start", [
                    ParameterDef("launch_type",  str,  True,  None, "Launch type (nav, slam, map)"),
                    ParameterDef("use_sim_time", bool, False, None, "Use simulation time"),
                    ParameterDef("map",          str,  False, None, "Map filename"),
                    ParameterDef("map_name",     str,  False, None, "Map name for map launch type"),
                ], ...)
"launch.stop":  CommandDef("launch_stop",  [ParameterDef("launch_type", str, True, ...)], ...)
```

## Parameter Design for `launch.start`

`launch.start` has four parameters but only `launch_type` is required. The optional parameters (`use_sim_time`, `map`, `map_name`) are passed as `**kwargs` through `RobotController.launch_start` into `ProcessApi.launch_by_type`, which adds non-None values to the command template.

This means the CLI user writes:

```
launch start nav --map basement
```

and `ProcessApi` resolves `basement` to the full YAML path under `maps_dir` and appends `map:=/full/path/basement.yaml` to the ros2 launch command.

## What `launch.list` Shows

`launch.list` calls `RobotController.launch_list`, which queries `ProcessApi.get_available_launch_types()` and formats a table:

```
NAME            DESCRIPTION
----------------------------------------------------------------------
nav             Nav2 navigation stack
slam            SLAM Toolbox online async
map             Map server
```

These names come directly from the `launch_templates` keys in `config.yaml`. If the config has no templates, this command returns "No launch templates available."

## Observations

- `launch.info` returns the raw command template, which exposes implementation details (full `ros2 launch` command strings). This is useful for debugging but might be surprising to end users.
- There is no `launch.status` command to see which launch types are currently running. `robot status` includes this information but it's buried in a larger status dump.
- `map_name` and `map` are distinct parameters that behave differently in `ProcessApi.launch_by_type` — `map` is a map file for nav, while `map_name` is for the map server launch type. This is a confusing API that could be unified.
