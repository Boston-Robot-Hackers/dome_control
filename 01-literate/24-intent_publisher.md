---
version: "1.0"
generated: "2026-05-06"
---

# IntentPublisher

`control/commands/intent_publisher.py` is the thin layer between `CommandDispatcher` and the `/intent` ROS2 topic. It accepts an injected `publish_fn` so unit tests stay No-ROS, while production uses `IntentApi` lazily.

## Interface

```python
class IntentPublisher:
    def __init__(self, publish_fn: Callable[[str], None] | None = None): ...
    def publish(self, name: str, source: str = "cli", slots: dict | None = None) -> None: ...
    def get_api(self): ...
```

## Publish Path

```python
def publish(self, name: str, source: str = "cli", slots: dict | None = None) -> None:
    payload = json.dumps({"name": name, "source": source, "slots": slots or {}})
    if self.publish_fn is not None:
        self.publish_fn(payload)
    else:
        self.get_api().publish(name, source, slots or {})
```

When `publish_fn` is injected, the JSON payload string is passed to it directly. This is the test path — callers capture the list and assert on parsed JSON. When `publish_fn` is `None`, `get_api()` creates an `IntentApi` instance on first call (lazy init avoids importing `rclpy` at module load).

## Testing Pattern

```python
published = []
pub = IntentPublisher(publish_fn=published.append)
dispatcher = CommandDispatcher(rc, intent_publisher=pub)
dispatcher.dispatch_text("scene describe")
assert json.loads(published[0])["name"] == "describe_scene"
```

The list collects raw JSON strings. Tests parse them to assert on structure.

## CommandDispatcher Integration

`CommandDispatcher.__init__` accepts `intent_publisher=None`. When `None`, `publish_intent` creates an `IntentPublisher()` inline (no injection, production default). When injected, the passed instance is used for all intent publishes.

## Observations

- `get_api()` creates a new `IntentApi(ConfigManager())`. In a long-running process, the `api` attribute caches the instance after first use.
- The split between `IntentPublisher` (JSON serialization + injection seam) and `IntentApi` (actual ROS2 publisher) exists so `IntentPublisher` remains importable without ROS2.
