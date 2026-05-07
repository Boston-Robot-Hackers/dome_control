---
version: "1.1"
generated: "2026-05-07"
---

# PerceptionBehavior — Perception Intent Handler

## Purpose

`PerceptionBehavior` handles perception-domain intents routed from `BehaviorManagerNode`. It either calls a ROS2 service (`describe_scene`) or reads cached sensor data (`list_objects`) and publishes results to `/announcement`.

## Intent Routing

Three intents are handled:

```python
PERCEPTION_INTENTS = {"describe_scene", "count_objects", "list_objects"}
```

```python
    def execute(self, intent: Intent, node=None) -> None:
        if intent.name == "describe_scene":
            self.call_describe_scene()
        elif intent.name == "list_objects":
            self.report_detections()
        elif intent.name == "count_objects":
            self.node.get_logger().warn("count_objects intent not yet implemented")
```

## describe_scene: Async Service Call

The `/describe_scene` service (provided by `describe_scene_stub` or a real vision node) returns a string description via `Trigger`. The call is async — the result arrives in `on_describe_scene_done`:

```python
    def call_describe_scene(self) -> None:
        if not self.node.describe_scene_client.service_is_ready():
            self.node.get_logger().warn("/describe_scene service is not available")
            return
        from std_srvs.srv import Trigger
        future = self.node.describe_scene_client.call_async(Trigger.Request())
        future.add_done_callback(self.on_describe_scene_done)
```

## list_objects: Reading Cached Detections

`BehaviorManagerNode` caches the latest `Detection2DArray` from `/oak/detections`. `report_detections` reads that cache, picks the highest-scoring hypothesis per detection, and formats a sentence:

```python
    def report_detections(self) -> None:
        detections = getattr(self.node, "latest_detections", None)
        if detections is None or not detections.detections:
            self.publish_announcement("No objects detected.")
            return
        parts = []
        for det in detections.detections:
            if det.results:
                best = max(det.results, key=lambda r: r.hypothesis.score)
                label = best.hypothesis.class_id
                score = round(best.hypothesis.score, 2)
                parts.append(f"{label} {score}")
        text = "I see: " + ", ".join(parts) if parts else "No objects detected."
        self.publish_announcement(text)
```

## Observations

- `getattr(self.node, "latest_detections", None)` is defensive — works whether oak is running or not.
- `count_objects` is registered but unimplemented. Should be removed or implemented.
- The lazy `from std_srvs.srv import Trigger` import avoids pulling rclpy at module load, keeping the class testable without ROS. A top-level import would be cleaner if the no-rclpy constraint is lifted.
