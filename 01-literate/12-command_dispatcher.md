---
version: "1.1"
generated: "2026-05-04"
---

# CommandDispatcher: Command Registry and Execution

`CommandDispatcher` is the single entry point for all command execution. The CLI, REST API, and any future interface all call `dispatcher.execute(name, params)` and get back a `CommandResponse`. The dispatcher handles parameter validation, type coercion, and method dispatch — callers never touch `RobotController` methods directly.

## Registry as a Dict

The command registry is a plain `dict[str, CommandDef]` built at construction time from module-level builder functions:

```python
def _build_command_registry(self) -> dict[str, cd.CommandDef]:
    commands = {}
    commands.update(mov_cmd.build_movement_commands())
    commands.update(ctrl_cmd.build_control_commands())
    commands.update(nav_cmd.build_navigation_commands())
    commands.update(lch_cmd.build_launch_commands())
    commands.update(sys_cmd.build_system_commands())
    commands.update(intent_cmd.build_intent_commands())
    commands.update(sem_cmd.build_semantic_commands())
    return commands
```

Each `build_*` function returns a dict of `"group.command" → CommandDef`. The flat merge means duplicate names from different modules would silently shadow each other — something to watch when adding new command groups.

## The Execute Path

```
dispatcher.execute("move.distance", {"distance": "1.5"})
    │
    ├── look up CommandDef in registry
    ├── _validate_parameters → coerce "1.5" → 1.5 (float)
    ├── getattr(robot_controller, "move_distance")
    └── method(distance=1.5) → CommandResponse
```

```python
def execute(self, command_name: str, params: dict) -> rc.CommandResponse:
    if command_name not in self.commands:
        return rc.CommandResponse(success=False, message=f"Unknown command: {command_name}")

    command_def = self.commands[command_name]
    validated_params = self._validate_parameters(command_def, params)
    method = getattr(self.robot_controller, command_def.method_name)
    result = method(**validated_params) if validated_params else method()

    if isinstance(result, rc.CommandResponse):
        return result
    return rc.CommandResponse(success=True, message=str(result) if result is not None else "Command completed")
```

The `isinstance` check at the end handles the case where a method returns `CommandResponse` directly (the norm) vs. something else (e.g., `None` from a method that hasn't been updated yet).

## Parameter Validation and Coercion

`_validate_parameters` enforces required params and hands each value to `_convert_parameter_value`:

```python
def _convert_parameter_value(self, param_def, value):
    if param_def.param_type == bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if param_def.param_type == str:
        return str(value)
    return param_def.param_type(value)
```

Boolean gets special treatment because Python's `bool("false")` is `True` — a common trap. Everything else is a direct constructor call (`float("1.5")`, `int("3")`).

Optional parameters with a `None` default are simply omitted from the validated dict if not provided, so the method's own default handling applies.

## Query Methods

Three methods support introspection:

```python
def list_commands(self, group: str | None = None) -> list[str]
def get_command_info(self, command_name: str) -> cd.CommandDef | None
def get_groups(self) -> list[str]
```

These power the CLI help display and allow the REST API to describe available commands without hardcoding.

## Observations

- **Silent shadowing.** If two `build_*` functions return the same key, the last one wins silently. A uniqueness check during construction would catch this at startup.
- **`bare except Exception` in execute.** The catch-all around `method(**validated_params)` swallows `KeyboardInterrupt` and other non-`Exception` exceptions. Should be tightened to catch only expected runtime errors.
- **Method lookup via `getattr`.** If a `CommandDef.method_name` doesn't exist on `RobotController`, it returns `CommandResponse(False, "Method ... not found")` at runtime rather than failing at registry build time. A startup validation pass would catch stale `method_name` references.
