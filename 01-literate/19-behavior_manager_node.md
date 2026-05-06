---
version: "2.0"
generated: "2026-05-06"
---

# BehaviorManagerNode

`behavior_manager_node.py` is the ROS2 shell around `IntentParser` and the domain behavior handlers. It wires the behavior logic to ROS2 topics and services.

## Node Topology

```
/intent (std_msgs/String)
        ↓ on_intent → IntentParser.parse_intent
  BehaviorManagerNode
    ├── MotionBehavior.execute(intent, node)
    │       ↓ RobotController (stop, drive_square, explore)
    └── PerceptionBehavior.execute(intent, node)
            ↓ call_describe_scene (async service call)
      /describe_scene (std_srvs/Trigger)
            ↓ on_describe_scene_done
      /announcement (control/Announcement)
```

The node subscribes to `/intent`, routes the parsed intent to the first matching handler, and each handler drives its own downstream I/O.

## Handler Registration

Handlers are registered as a list in `__init__`:

```python
rc = RobotController(ConfigManager())
self.handlers = [
    MotionBehavior(rc),
    PerceptionBehavior(self),
]
```

`MotionBehavior` receives a `RobotController` instance. `PerceptionBehavior` receives the node itself so it can access the service client, publisher, and logger.

## Intent Dispatch

```python
def on_intent(self, msg: String) -> None:
    try:
        intent = self.parser.parse_intent(msg.data)
    except ValueError as exc:
        self.get_logger().warn(str(exc))
        return

    for handler in self.handlers:
        if handler.handles(intent.name):
            handler.execute(intent, self)
            return

    self.get_logger().warn(f"Unhandled intent: {intent.name}")
```

The loop tries each handler in registration order. First match wins. Unrecognized intent names log a warning and are dropped — no crash, no retry.

## Adding a New Domain

To add a new behavior domain:

1. Create `control/behaviors/my_domain_behavior.py` with `handles()` and `execute()`.
2. Append an instance to `self.handlers` in `BehaviorManagerNode.__init__`.
3. No changes to `on_intent` are needed.

## Observations

- There is no `/intent` acknowledgement. Publishers have no way to know whether the intent was received and acted on.
- Handler order matters. The first handler whose `handles()` returns `True` claims the intent; later handlers never see it.
- `PerceptionBehavior` receives the whole node. A narrower interface (publisher + client + logger) would reduce coupling.
