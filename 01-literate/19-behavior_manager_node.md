---
version: "1.1"
generated: "2026-05-07"
---

# BehaviorManagerNode — Intent Router

## Purpose

`BehaviorManagerNode` is the central ROS2 node that receives structured intents from `/intent` and dispatches them to domain-specific behavior handlers. It also caches sensor data from `/oak/detections` for use by `PerceptionBehavior`.

## Subscriptions and Publishers

```python
self.intent_sub = self.create_subscription(
    String, "/intent", self.on_intent, 10
)
self.detections_sub = self.create_subscription(
    Detection2DArray, "/oak/detections", self.on_detections, 10
)
self.latest_detections: Detection2DArray | None = None
self.announcement_pub = self.create_publisher(
    AnnouncementMsg, "/announcement", 10
)
self.describe_scene_client = self.create_client(Trigger, "/describe_scene")
```

`/oak/detections` is optional — the subscription exists whether or not oak is running. When no oak node is present, `latest_detections` stays `None` and `PerceptionBehavior.report_detections()` returns "No objects detected." cleanly.

## Detection Cache

A one-liner callback keeps the latest frame:

```python
    def on_detections(self, msg: Detection2DArray) -> None:
        self.latest_detections = msg
```

## Intent Dispatch

Intents are parsed from JSON, matched against handlers, and executed. `get_help` is handled inline because it requires no domain knowledge:

```python
    def on_intent(self, msg: String) -> None:
        try:
            intent = self.parser.parse_intent(msg.data)
        except ValueError as exc:
            self.get_logger().warn(str(exc))
            return

        if intent.name == "get_help":
            ...announce command list...
            return

        for handler in self.handlers:
            if handler.handles(intent.name):
                handler.execute(intent, self)
                return

        self.get_logger().warn(f"Unhandled intent: {intent.name}")
```

## Handler Registration

```python
self.handlers = [
    MotionBehavior(rc),
    PerceptionBehavior(self),
]
```

Handlers are checked in order. Adding new domains means appending to this list.

## Observations

- `get_help` handled inline is a mild violation of the handler pattern. A `HelpBehavior` would be consistent.
- `latest_detections` is mutable shared state updated by a ROS2 callback and read by a behavior. In a multi-threaded executor this is a race; the default single-threaded executor makes it safe.
