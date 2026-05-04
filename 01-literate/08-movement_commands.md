---
version: "1.0"
generated: "2026-05-04"
---

# Movement Commands

`movement_commands.py` defines the command registry entries for all robot motion commands. It is the translation layer between user-facing CLI vocabulary and `RobotController` method names.

## What This Module Is and Isn't

This module contains *no logic*. It returns a dict of `CommandDef` objects. All motion implementation is in `RobotController` and `MovementApi`. The purpose of this file is to declare:

- What command names the CLI recognises
- What parameters each command expects
- Which `RobotController` method to call

## The Registry

```python
def build_movement_commands() -> dict[str, cd.CommandDef]:
    return {
        "move.distance": CommandDef("move_distance", [ParameterDef("distance", float, True, ...)], ...),
        "move.time":     CommandDef("move_for_time",  [ParameterDef("seconds",  float, True, ...)], ...),
        "turn.time":     CommandDef("turn_for_time",  [ParameterDef("seconds",  float, True, ...)], ...),
        "turn.radians":  CommandDef("turn_radians",   [ParameterDef("radians",  float, True, ...)], ...),
        "turn.degrees":  CommandDef("turn_degrees",   [ParameterDef("degrees",  float, True, ...)], ...),
        "move.forward":  CommandDef("move_forward",   [ParameterDef("meters",   float, True, ...)], ...),
        "move.backward": CommandDef("move_backward",  [ParameterDef("meters",   float, True, ...)], ...),
        "turn.clockwise":        CommandDef("turn_clockwise",        [ParameterDef("degrees", float, True, ...)], ...),
        "turn.counterclockwise": CommandDef("turn_counterclockwise", [ParameterDef("degrees", float, True, ...)], ...),
    }
```

## Command Name Convention

Keys use `group.subcommand` dot notation. `CommandDispatcher` treats the dot as a separator between the command group and the subcommand variant. `SimpleParser` maps user input `"move forward 1.5"` to the key `"move.forward"` by joining the first two resolved tokens with a dot.

## Semantic Duplication

Notice that `move.distance` / `move.forward` / `move.backward` all ultimately call `move_dist` on `MovementApi`, with `move.forward` forcing positive and `move.backward` forcing negative distance. This redundancy is intentional: it lets users speak in whichever vocabulary feels natural (`move distance -1.0` vs `move backward 1.0`).

## Observations

- All parameters are `required=True` with `default=None`. There are no optional motion parameters. Adding defaults (e.g., a default distance of 1.0 metre) would make one-word commands like `move forward` work.
- `turn.radians` and `turn.degrees` both exist, which is good for users who think in either unit. They call different `RobotController` methods which in turn call different `MovementApi` methods (`turn_amount` for radians, `turn_degrees` which converts and calls `turn_amount`).
