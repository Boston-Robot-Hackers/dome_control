---
version: "1.0"
generated: "2026-05-06"
---

# PerceptionBehavior

`control/behaviors/perception_behavior.py` handles perception-domain intents via async ROS2 service calls. It holds no direct ROS2 imports at module load — `std_srvs.srv.Trigger` is imported lazily inside `call_describe_scene` to keep the module importable in no-ROS test environments.

## Interface

```python
PERCEPTION_INTENTS = {"describe_scene", "count_objects"}

class PerceptionBehavior:
    def __init__(self, node): ...
    def handles(self, intent_name: str) -> bool: ...
    def execute(self, intent: Intent, node=None) -> None: ...
```

`PerceptionBehavior` receives the owning `BehaviorManagerNode` at construction. It needs the node for three things: the `describe_scene_client`, the `announcement_pub`, and the logger.

## Async Service Call Flow

```
execute("describe_scene")
    → call_describe_scene()
        → service_is_ready() check
        → lazy import std_srvs.srv.Trigger
        → call_async(Trigger.Request())
        → future.add_done_callback(on_describe_scene_done)
    on_describe_scene_done(future)
        → future.result() → response
        → publish_announcement(response.message)
    publish_announcement(text)
        → make_announcement_msg(text)
        → announcement_pub.publish(msg)
```

The call is non-blocking. `call_async` returns immediately; the callback fires when the ROS2 executor delivers the response. Blocking service calls inside spin callbacks would deadlock the executor.

## Error Handling

`on_describe_scene_done` handles two failure modes:

1. **Exception from `future.result()`** (timeout, network error): logs error, returns.
2. **`response.success == False`**: logs warning, skips announcement.

In both cases the node continues running. There is no retry or queuing.

## Observations

- `count_objects` logs "not yet implemented" and does nothing. The intent routes without warning.
- `PerceptionBehavior` receives the whole node. A narrower interface (client + publisher + logger) would reduce coupling.
- `std_srvs.srv.Trigger` has no parameters. Passing `slots` data (e.g., object_type) to the scene service would require a richer service type.
