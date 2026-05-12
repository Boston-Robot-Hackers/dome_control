---
version: "1.2"
generated: "2026-05-12"
---

# BehaviorManagerNode — Intent Router

## Purpose

`BehaviorManagerNode` is the central ROS2 node that receives structured intents from `/intent` and dispatches them to domain-specific behavior handlers. It also caches sensor data from `/oak/detections` and loads vision class profiles for label resolution.

## Initialization: Handlers and Vision Config

At startup the node wires two behavior handlers and optionally loads class profiles from `dome_vision`:

```python
rc = RobotController(ConfigManager.create(DEFAULT_CONFIG))
self.handlers = [
    MotionBehavior(rc),
    PerceptionBehavior(self),
]
```

Class profiles are loaded from a YAML file whose path is settable via a ROS2 parameter, defaulting to the `dome_vision` config location:

```python
self.declare_parameter("class_profiles_path", DEFAULT_VISION_CONFIG)
vision_config_path = self.get_parameter("class_profiles_path").get_parameter_value().string_value
self.profiles: dict = {}
self.label_map: dict = {}
try:
    from dome_vision.class_profiles import build_label_map, load_class_profiles
    self.profiles = load_class_profiles(vision_config_path)
    self.label_map = build_label_map(self.profiles)
except Exception as exc:
    self.get_logger().warn(f"Could not load class profiles from {vision_config_path}: {exc}")
```

The `try/except` means the node runs without `dome_vision` installed — perception commands degrade to raw class IDs rather than failing entirely.

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

```mermaid
flowchart TD
    A[/intent topic] --> B[parse_intent]
    B -- ValueError --> C[log warn]
    B -- Intent --> D{get_help?}
    D -- yes --> E[announce command list]
    D -- no --> F[MotionBehavior.handles?]
    F -- yes --> G[MotionBehavior.execute]
    F -- no --> H[PerceptionBehavior.handles?]
    H -- yes --> I[PerceptionBehavior.execute]
    H -- no --> J[log unhandled]
```

## Observations

- `get_help` handled inline is a mild violation of the handler pattern. A `HelpBehavior` would be consistent.
- `latest_detections` is mutable shared state updated by a ROS2 callback and read by a behavior. In a multi-threaded executor this is a race; the default single-threaded executor makes it safe.
- `profiles` and `label_map` are set on the node so `PerceptionBehavior` can access them via `self.node`. This is a form of implicit coupling — `PerceptionBehavior` must know the node has these attributes. An explicit dependency injection would be cleaner.
- The `dome_vision` import is inside a `try/except` at init time, not deferred. If `dome_vision` is importable but the YAML is malformed, the node still starts with empty profiles rather than crashing.
