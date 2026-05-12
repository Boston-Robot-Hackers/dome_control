---
version: "2.1"
generated: "2026-05-12"
---

# CommandDispatcher: Command Registry and Execution

`CommandDispatcher` is the single entry point for all command execution. The CLI, REST API, and any future interface call `dispatcher.execute(name, params)` or `dispatcher.dispatch_text(text)` and get back a `CommandResponse`. The dispatcher handles parameter validation, type coercion, and method dispatch — callers never touch `RobotController` methods directly.

## Registry as a Dict

The command registry is a plain `dict[str, CommandDef]` built at construction time:

```python
def _build_command_registry(self) -> dict[str, cd.CommandDef]:
    commands = {}
    commands.update(mov_cmd.build_movement_commands())
    commands.update(ctrl_cmd.build_control_commands())
    commands.update(nav_cmd.build_navigation_commands())
    commands.update(lch_cmd.build_launch_commands())
    commands.update(sys_cmd.build_system_commands())
    return commands
```

Each `build_*` function returns a dict of `"group.command" → CommandDef`. Intent commands and semantic commands were in this registry prior to F15/T07; they are now handled entirely by `dispatch_text` routing. The flat merge means duplicate names from different modules would silently shadow each other.

## The Execute Path

```
dispatcher.execute("move.forward", {"meters": "1.5"})
    │
    ├── look up CommandDef in registry
    ├── _validate_parameters → coerce "1.5" → 1.5 (float)
    ├── getattr(robot_controller, "move_forward")
    └── method(meters=1.5) → CommandResponse
```

## dispatch_text: Text-to-Command Routing

`dispatch_text(text)` is the entry point for free-form text input (CLI, voice transcripts):

```python
def dispatch_text(self, text: str) -> rc.CommandResponse:
    tokens = text.strip().split()
    command = resolve_keyword(tokens[0])
    ...
    intent_name = BEHAVIOR_COMMANDS.get(command_name)
    if intent_name is not None:
        reply = self.publish_intent(intent_name, slots)
        msg = reply if reply is not None else f"Intent published: {intent_name}"
        return rc.CommandResponse(True, msg)
    ...
    return self.execute(command_name, params)
```

Two routing paths:

- **Behavior path** — command name is in `BEHAVIOR_COMMANDS` → publish to `/intent` via `IntentPublisher`, return immediately.
- **Direct path** — everything else → look up `CommandDef`, validate params, call `RobotController` method.

## BEHAVIOR_COMMANDS

Maps CLI command names to intent names:

```python
BEHAVIOR_COMMANDS: dict[str, str] = {
    "intent.stop":           "stop",
    "intent.explore":        "explore",
    "intent.describe_scene": "describe_scene",
    "intent.count_objects":  "count_objects",
    "intent.list_objects":   "list_objects",
    "scene.describe":        "describe_scene",
    "scene.count":           "count_objects",
    "scene.objects":         "list_objects",
}
```

`scene.*` forms are preferred interactive vocabulary; `intent.*` forms kept for scripting. `publish_intent` returns `str | None` — if `IntentApi` waited for a reply (query intents), the reply text comes back and replaces the default "Intent published" message in the `CommandResponse`.

## Abbreviation Resolution

`ABBREV_TO_FULL` and `FULL_NAMES` are module-level constants. `resolve_keyword` expands short tokens:

```python
ABBREV_TO_FULL = {"m": "move", "fwd": "forward", "stp": "stop", ...}
FULL_NAMES = set(ABBREV_TO_FULL.values())

def resolve_keyword(word: str) -> str:
    if word in FULL_NAMES:
        return word
    return ABBREV_TO_FULL.get(word, word)
```

Unknown tokens pass through unchanged; errors surface at execution time.

## Subcommand Detection

After resolving the first token, the parser checks whether the second token forms a compound command:

```python
second = resolve_keyword(tokens[1])
candidate = f"{command}.{second}"
in_registry = candidate in self.commands or candidate in BEHAVIOR_COMMANDS
if second in FULL_NAMES or second != tokens[1] or in_registry:
    command_name = candidate   # compound: "move.forward"
    args = [parse_value(t) for t in tokens[2:]]
else:
    command_name = command     # simple: "stop"
    args = [parse_value(t) for t in tokens[1:]]
```

The `in_registry` check ensures `scene describe` routes correctly even though "describe" is not in `FULL_NAMES`.

## IntentPublisher Injection

```python
def __init__(self, robot_controller, intent_publisher=None):
    ...
    self.intent_publisher = intent_publisher
```

In production, leave `intent_publisher=None` — `publish_intent` creates an `IntentPublisher` lazily. In tests, pass `IntentPublisher(publish_fn=published.append)` to capture published payloads without ROS2.

## Parameter Validation and Coercion

`_convert_parameter_value` handles booleans specially:

```python
if param_def.param_type == bool:
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)
```

Python's `bool("false")` is `True`, so string booleans need explicit mapping.

## Observations

- **Silent shadowing.** Duplicate keys across `build_*` functions are silently overwritten.
- **Method lookup at runtime.** A stale `method_name` in a `CommandDef` fails at call time, not at registry build time.
