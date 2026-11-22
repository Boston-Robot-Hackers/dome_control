---
version: "2.0"
generated: "2026-11-22"
---

# IntentPublisher — a seam for testing the behavior path

`IntentPublisher` (`commands/intent_publisher.py`) sits between
`CommandDispatcher` and `IntentApi`. Its only job is to let tests check
what the dispatcher would publish without a ROS graph.

## Two modes behind one method

```python
def publish(self, name, source="cli", slots=None) -> str | None:
    payload = json.dumps({"name": name, "source": source, "slots": slots or {}})
    if self.publish_fn is not None:
        self.publish_fn(payload)
        return None
    return self.get_api().publish(name, source, slots or {})
```

- **Test mode**: construct with `publish_fn=captured.append`, and every
  intent becomes a JSON string in a list. No reply is ever returned.
- **Production mode**: `IntentApi` is created lazily on first use and does
  the real publish-and-wait.

`SimpleCLI` calls `get_api()` once at startup to "warm up". Creating the
node early gives DDS time to discover the `behavior_manager` subscriber
before the first intent is sent, so that first intent isn't lost.

## The JSON is built twice

In production mode the `payload` string is built and then discarded,
because `IntentApi.publish` builds its own JSON from the same three values.
The two encodings can drift. If the format ever changes in one place, tests
using `publish_fn` keep passing against a format production no longer
sends.

## Observations

1. **Build the payload in one place.** Have `IntentApi.publish` accept the
   payload, or put the JSON encoding in a shared function (it is the
   inverse of `IntentParser.parse_intent`, so it belongs next to it).
2. **Unify with `RobotController.intent`.** The controller creates its own
   `IntentApi` for `publish_intent_*` and the mission commands. Inject this
   one publisher into both, so the CLI has one intent node, warmed up once.
   The controller's version also sleeps 0.5 s on first use instead of
   warming up.
3. **The dispatcher's fallback leaks nodes.** When no publisher is
   injected, `CommandDispatcher.publish_intent` builds a fresh
   `IntentPublisher`, and so a fresh `IntentApi` node, on **every call**,
   and never destroys it (issue I05). Make the publisher a required
   dependency.
