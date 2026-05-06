---
version: "1.2"
generated: "2026-05-06"
---

# IntentParser: Pure Intent Parsing Logic

`behavior_manager.py` holds `IntentParser` — pure logic for parsing and validating intents with no ROS2 dependency. The name `BehaviorManager` was retired in F15/T01; the class is now `IntentParser` to reflect its single responsibility.

The ROS2 node layer (`BehaviorManagerNode`) handles subscriptions and callbacks; `IntentParser` handles only the JSON parsing semantics. Tests for intent parsing run without a ROS2 context.

## The Intent Dataclass

```python
@dataclass
class Intent:
    name: str
    source: str
    slots: dict
```

An intent has a name (what to do), a source (who asked), and slots (parameters). The slots dict is open-ended — different intents carry different slot keys. Validation of slot contents is left to the downstream handler.

## Parsing with Strict Validation

`parse_intent` takes a raw JSON string — as it arrives over a ROS2 topic — and returns a typed `Intent` or raises `ValueError`:

```python
def parse_intent(self, payload: str) -> Intent:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid intent JSON: {exc.msg}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Intent payload must be a JSON object")

    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("Intent field 'name' must be a non-empty string")

    source = raw.get("source", "unknown")
    slots = raw.get("slots", {})
    if not isinstance(slots, dict):
        raise ValueError("Intent field 'slots' must be an object")

    return Intent(name=name, source=source, slots=slots)
```

Each check raises with a descriptive message. The caller (the ROS2 node) can log the error and discard the message without crashing.

## Announcement Helpers

Two helpers are re-exported from this module:

```python
from control.announcement_contract import (
    make_announcement_msg,
    make_announcement_payload,
)
```

The actual implementation lives in `announcement_contract.py` to avoid a circular dependency with the ROS2 message type.

## Observations

- **No slot validation.** `parse_intent` validates structure but not slot contents. An intent `{"name": "count_objects", "slots": {}}` (missing `object_type`) will parse successfully and fail later.
- **`source` default is "unknown".** Could be required rather than silently defaulted.
- **Single method class.** `IntentParser` has one public method. The class form is kept for future expansion (e.g., intent history, rate limiting).
