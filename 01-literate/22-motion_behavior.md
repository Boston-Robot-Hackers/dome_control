---
version: "2.0"
generated: "2026-05-06"
---

# MotionBehavior

`dome_control/behaviors/motion_behavior.py` handles motion-domain intents. It has no ROS2 dependency — all execution goes through `RobotController`, except for `get_status` which needs to publish an announcement via the node.

## Interface

```python
MOTION_INTENTS = {"stop", "explore", "drive_square", "turn_right", "turn_left", "get_status"}
TURN_DEGREES = 90

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
    elif intent.name == "turn_right":
        self.rc.turn_clockwise(TURN_DEGREES)
    elif intent.name == "turn_left":
        self.rc.turn_counterclockwise(TURN_DEGREES)
    elif intent.name == "get_status" and node is not None:
        result = self.rc.get_robot_status()
        ...
        node.announcement_pub.publish(msg)
```

## Turn Commands

`turn_right` and `turn_left` delegate to `RobotController.turn_clockwise` / `turn_counterclockwise`, which convert degrees to radians and call `MovementApi.turn_degrees`. The constant `TURN_DEGREES = 90` is defined at module level so it can be adjusted without searching inside the dispatch logic.

Sign convention follows ROS standard: counterclockwise is positive angular velocity, so `turn_counterclockwise` passes a positive angle and `turn_clockwise` negates it.

## Status Announcement

`get_status` is the one intent that needs the `node` reference, to publish a spoken response:

```python
elif intent.name == "get_status" and node is not None:
    result = self.rc.get_robot_status()
    status = result.data.get("status", {}) if result.data else {}
    speeds = status.get("speeds", {})
    text = (
        f"linear speed {speeds.get('linear', 'unknown')}, "
        f"angular speed {speeds.get('angular', 'unknown')}"
    )
    msg = make_announcement_msg(text, priority=PRIORITY_QUERY_REPLY, source="motion_behavior")
    node.announcement_pub.publish(msg)
```

The guard `and node is not None` means the intent is silently ignored if called without a node (e.g. from tests or CLI). This keeps the handler safe without requiring a real publisher in every context.

## Slot Handling

`drive_square` reads `slots["meters"]` with a default of `1.0`. All other current motion intents are parameterless.

## Observations

- `explore` is a no-op. The implementation slot exists so the intent routes correctly without an "Unhandled intent" warning.
- `cmd_vel_helper` blocks the behavior_manager callback thread for the full turn duration. No other intents are processed during a turn.
- Adding a new motion intent requires: adding the name to `MOTION_INTENTS` and adding an `elif` branch in `execute`.
