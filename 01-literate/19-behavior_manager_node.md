---
version: "3.0"
generated: "2026-05-06"
---

# BehaviorManagerNode

`behavior_manager_node.py` is the ROS2 shell around `IntentParser` and the domain behavior handlers. It wires behavior logic to ROS2 topics and services.

## Node Topology

```
/intent (std_msgs/String)
        ↓ on_intent → IntentParser.parse_intent
  BehaviorManagerNode
    ├── get_help (inline) → /announcement
    ├── MotionBehavior.execute(intent, node)
    │       ↓ RobotController (stop, turn_right, turn_left, get_status, drive_square, explore)
    └── PerceptionBehavior.execute(intent, node)
            ↓ call_describe_scene (async service call)
      /describe_scene (std_srvs/Trigger)
            ↓ on_describe_scene_done
      /announcement (control/Announcement)
```

## Handler Registration

Handlers are registered as a list in `__init__`. `ConfigManager.create()` loads the YAML config file before passing it to `RobotController` — using the bare constructor would skip config loading:

```python
rc = RobotController(ConfigManager.create(DEFAULT_CONFIG))
self.handlers = [
    MotionBehavior(rc),
    PerceptionBehavior(self),
]
```

`MotionBehavior` receives a `RobotController` instance. `PerceptionBehavior` receives the node itself so it can access the service client, publisher, and logger.

## Intent Dispatch

The `get_help` intent is handled inline rather than as a behavior handler, because it only needs the `announcement_pub` already on the node:

```python
def on_intent(self, msg: String) -> None:
    try:
        intent = self.parser.parse_intent(msg.data)
    except ValueError as exc:
        self.get_logger().warn(str(exc))
        return

    if intent.name == "get_help":
        msg = make_announcement_msg(
            "commands are stop, explore, describe, right, left, status and help",
            priority=PRIORITY_QUERY_REPLY,
            source="behavior_manager",
        )
        self.announcement_pub.publish(msg)
        return

    for handler in self.handlers:
        if handler.handles(intent.name):
            handler.execute(intent, self)
            return

    self.get_logger().warn(f"Unhandled intent: {intent.name}")
```

The loop tries each handler in registration order. First match wins. Unrecognized intent names log a warning and are dropped.

## Shutdown Guard

```python
finally:
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
```

The `rclpy.ok()` guard prevents a double-shutdown crash. ROS2 installs a SIGINT handler that calls `shutdown()` automatically; without the guard, the `finally` block would call it a second time, raising `RCLError`.

## Adding a New Domain

To add a new behavior domain:

1. Create `control/behaviors/my_domain_behavior.py` with `handles()` and `execute()`.
2. Append an instance to `self.handlers` in `BehaviorManagerNode.__init__`.
3. No changes to `on_intent` are needed.

## Observations

- There is no `/intent` acknowledgement. Publishers have no way to know whether the intent was received and acted on.
- Handler order matters. The first handler whose `handles()` returns `True` claims the intent; later handlers never see it.
- `PerceptionBehavior` receives the whole node. A narrower interface (publisher + client + logger) would reduce coupling.
- `MotionBehavior.execute` blocks the callback thread during turns. No other intents are processed while the robot is turning.
