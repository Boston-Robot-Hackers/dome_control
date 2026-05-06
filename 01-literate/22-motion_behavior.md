---
version: "1.0"
generated: "2026-05-06"
---

# MotionBehavior

`control/behaviors/motion_behavior.py` handles motion-domain intents. It has no ROS2 dependency — all execution goes through `RobotController`.

## Interface

```python
MOTION_INTENTS = {"stop", "explore", "drive_square"}

class MotionBehavior:
    def __init__(self, robot_controller): ...
    def handles(self, intent_name: str) -> bool: ...
    def execute(self, intent: Intent, node=None) -> None: ...
```

`handles` returns `True` for any name in `MOTION_INTENTS`. `execute` dispatches on `intent.name`:

```python
def execute(self, intent: Intent, node=None) -> None:
    if intent.name == "stop":
        self.rc.stop_robot()
    elif intent.name == "drive_square":
        meters = float(intent.slots.get("meters", 1.0))
        self.rc.script_square(meters)
    elif intent.name == "explore":
        pass  # not yet implemented
```

`node` is accepted but unused — the signature matches `PerceptionBehavior` so both handlers can be called uniformly by `BehaviorManagerNode`.

## Slot Handling

`drive_square` reads `slots["meters"]` with a default of `1.0`. All other current motion intents are parameterless. Slot validation is left to the caller; a missing or non-numeric `meters` will raise at the `float()` call.

## Observations

- `explore` is a no-op. The implementation slot exists so the intent routes correctly without an "Unhandled intent" warning.
- Adding a new motion intent requires: adding the name to `MOTION_INTENTS`, adding an `elif` branch in `execute`, and adding the intent name to `BEHAVIOR_COMMANDS` in `command_dispatcher.py` if CLI access is wanted.
