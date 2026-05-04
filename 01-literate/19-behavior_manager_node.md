---
version: "1.0"
generated: "2026-05-04"
---

# BehaviorManagerNode

`behavior_manager_node.py` is the ROS2 shell around `BehaviorManager`. It wires the behavior logic to the actual ROS2 topics and services.

## Node Topology

```
/intent (std_msgs/String)
        ↓ on_intent
  BehaviorManagerNode
        ↓ call_describe_scene (async service call)
  /describe_scene (std_srvs/Trigger)
        ↓ on_describe_scene_done
  publish_announcement
        ↓
  /announcement (control/Announcement)
```

The node subscribes to `/intent`, calls `/describe_scene` as a ROS2 service, and publishes the response to `/announcement`.

## Asynchronous Service Call

The `/describe_scene` call is non-blocking:

```python
def call_describe_scene(self) -> None:
    if not self.describe_scene_client.service_is_ready():
        self.get_logger().warn("/describe_scene service is not available")
        return
    future = self.describe_scene_client.call_async(Trigger.Request())
    future.add_done_callback(self.on_describe_scene_done)
```

`call_async` returns immediately; `on_describe_scene_done` is called by the ROS2 executor when the service responds. This is the correct pattern for ROS2 nodes — blocking service calls inside `spin` callbacks would deadlock the executor.

## Service Availability Check

`service_is_ready()` checks whether at least one server has registered for `/describe_scene`. If the `describe_scene_stub_node` (or the real implementation) is not running, the intent is silently dropped with a warning. There is no retry or queuing mechanism.

## Publishing Announcements

```python
def publish_announcement(self, text: str) -> None:
    msg = make_announcement_msg(text)
    self.announcement_pub.publish(msg)
    self.get_logger().info(text)
```

`make_announcement_msg` uses defaults from `announcement_contract.py`: `priority=PRIORITY_QUERY_REPLY`, `source="behavior_manager"`. These defaults are appropriate for scene descriptions but the node has no way to override them per-intent.

## Observations

- The node bypasses `BehaviorManager.handle_intent` and handles `describe_scene` inline. The intent is parsed via `self.manager.parse_intent` but then handled with a direct `if intent.name == "describe_scene"` check. The `BehaviorManager.handle_intent` method and this node's logic are parallel implementations that can drift.
- There is no `/intent` acknowledgement. The publisher (CLI or voice node) has no way to know whether the intent was received and acted upon.
- `Trigger` has no parameters. A richer service type would allow passing the intent's `slots` (e.g., `object_type` for `count_objects`) to the scene analysis service.
