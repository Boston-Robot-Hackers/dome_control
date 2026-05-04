---
version: "1.0"
generated: "2026-05-04"
---

# IntentApi

`intent_api.py` is the outbound side of the semantic behavior pipeline. It publishes structured intent messages to the `/intent` topic, which the `behavior_manager_node` consumes.

## Design

```python
class IntentApi(base.BaseApi):
    def __init__(self, config_manager: cm.ConfigManager = None):
        super().__init__("intent_api", config_manager)
        self.intent_pub = self.create_publisher(String, "/intent", 10)

    def publish(self, name: str, source: str, slots: dict) -> None:
        msg = String()
        msg.data = json.dumps({"name": name, "source": source, "slots": slots})
        self.intent_pub.publish(msg)
        self.log_info(f"Intent published: {msg.data}")
```

The intent is a JSON-serialised dict over `std_msgs/String`. The three fields match the `Intent` dataclass in `behavior_manager.py`:

| Field | Purpose |
|-------|---------|
| `name` | Action name, e.g. `"describe_scene"`, `"stop"` |
| `source` | Who published it — `"cli"` for CLI commands, `"voice"` for voice input |
| `slots` | Typed parameters, e.g. `{"object_type": "chair"}` |

## Why `std_msgs/String` and not a Custom Message

Using JSON over `String` means the intent topic requires no custom message type at compile time. Any ROS2 node — including Python scripts, shell tools, and the CLI — can publish or echo `/intent` without depending on this package's message definitions. The tradeoff is no compile-time type checking on the payload.

## Publisher Lifecycle in RobotController

`RobotController` lazily constructs `IntentApi` on first use:

```python
@property
def intent(self) -> IntentApi:
    if self._intent is None:
        self._intent = IntentApi(self.config)
        time.sleep(0.5)   # allow DDS discovery
    return self._intent
```

The `time.sleep(0.5)` after construction gives DDS time to discover the subscriber before the first publish. Without this delay, the first intent message may be dropped if the `behavior_manager_node` subscriber hasn't yet registered with the local DDS participant.

## Observations

- The `source` field is hardcoded to `"cli"` in all `RobotController` publish methods. If multiple interfaces (REST, TUI) are added later, passing the source as a parameter would be more correct.
- There is no acknowledgement mechanism. The CLI receives a `CommandResponse(True, ...)` immediately after publishing, regardless of whether the behavior manager received or handled the intent.
