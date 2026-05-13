---
version: "1.1"
generated: "2026-05-12"
---

# IntentPublisher

`dome_control/commands/intent_publisher.py` is the thin layer between `CommandDispatcher` and the `/intent` ROS2 topic. It accepts an injected `publish_fn` so unit tests stay No-ROS, while production uses `IntentApi` lazily.

## Interface

```python
class IntentPublisher:
    def __init__(self, publish_fn: Callable[[str], None] | None = None): ...
    def publish(self, name: str, source: str = "cli", slots: dict | None = None) -> str | None: ...
    def get_api(self): ...
```

## Publish Path

```python
def publish(self, name: str, source: str = "cli", slots: dict | None = None) -> str | None:
    payload = json.dumps({"name": name, "source": source, "slots": slots or {}})
    if self.publish_fn is not None:
        self.publish_fn(payload)
        return None
    return self.get_api().publish(name, source, slots or {})
```

Two paths:

- **Test path** (`publish_fn` injected): JSON payload is passed to the injected function (e.g. `list.append`). Returns `None` — tests assert on the captured JSON, not the return value.
- **Production path** (`publish_fn=None`): delegates to `IntentApi.publish`, which may wait for a `/announcement` reply for query intents and return the reply text. `get_api()` creates `IntentApi` lazily — avoids importing `rclpy` at module load.

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
