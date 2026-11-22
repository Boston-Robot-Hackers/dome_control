---
version: "2.0"
generated: "2026-11-22"
---

# BaseApi — the common parent of every ROS-facing API

`BaseApi` (`ros2_api/base_api.py`) is the superclass of `MovementApi`,
`CalibrationApi`, `ProcessApi`, `IntentApi` and `SpeechApi`. It makes each
API a `rclpy` `Node` and gives them three shared things:

- a reference to the `ConfigManager`
- logging helpers
- a bounds check

## Every API is its own node

```python
class BaseApi(Node, ABC):
    def __init__(self, node_name: str, config_manager: cm.ConfigManager = None):
        super().__init__(node_name)
        self.config = config_manager
```

Because each API subclasses `Node`, the CLI process ends up with one ROS
node per API: `movement_api`, `process_api`, `intent_api` and so on.
`RobotController` creates them lazily, so a session that only runs
`config get` never creates a movement node.

The `ABC` base is nominal: there are no abstract methods, so nothing forces
subclasses to implement anything.

## Logging that is half `print`

```python
def log_debug(self, message: str):
    self.get_logger().debug(message)

def log_info(self, message: str):
    print(message)

def log_warn(self, message: str):
    self.get_logger().warn(message)
```

`log_info` prints to stdout, while the other levels go through the ROS
logger. The reason is the CLI: info messages are user-facing progress
("Square side 2/4") and should appear without ROS log prefixes.

The cost is that inside a ROS node, such as when `MotionBehavior` drives a
square from within `behavior_manager`, info lines bypass the ROS log and
can't be filtered by level.

## A bounds check that warns

```python
def check_bounds(self, value, min_val, max_val, name) -> bool:
    if not (min_val <= value <= max_val):
        self.log_warn(f"{name} out of bounds: {value}. Must be [{min_val}, {max_val}]")
        return False
    return True
```

`MovementApi` uses this to refuse unsafe velocities. The refusal is only a
warning and a `False`. The caller then returns normally, so the CLI reports
"Moved forward 2 meters" even though the robot never moved (see
`05-movement_api.md`).

## Observations

1. **Return a reason, not just `False`.** Raise a `ValueError` from
   `check_bounds`, or have it return the message, so a refused move reaches
   the user as a failure.
2. **Logging is inconsistent.** Choose one rule, such as "APIs log through
   ROS and the CLI prints `CommandResponse.message`", and drop `print` from
   the API layer. `CalibrationApi` currently prints the same line twice
   because it calls both `print` and `log_info`.
3. **Drop `ABC`.** It promises an interface that doesn't exist.
4. **`config_manager=None` is never valid for the subclasses that use it.**
   `MovementApi` dereferences `self.config` immediately. Make the parameter
   required.
5. **Consider fewer nodes.** One node per API means separate discovery,
   separate parameter servers, and none of them are spun. A single CLI node
   with API objects that use it (composition rather than inheritance) would
   be lighter and would also address I05 (nodes never destroyed).
