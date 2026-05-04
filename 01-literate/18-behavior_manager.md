---
version: "1.1"
generated: "2026-05-04"
---

# BehaviorManager: Pure Intent Dispatch Logic

`BehaviorManager` holds the pure logic for parsing and validating intents — with no ROS2 dependency. This separation matters: the ROS2 node layer (`BehaviorManagerNode`) handles subscriptions and callbacks; `BehaviorManager` handles the semantics. Tests for intent parsing run in milliseconds without a ROS2 context.

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

Each check raises with a descriptive message. The caller (the ROS2 node) can log the error and discard the message without crashing the node.

## Announcement Helpers

Two helpers live alongside `BehaviorManager` and are re-exported from this module:

```python
from control.announcement_contract import (
    make_announcement_msg,
    make_announcement_payload,
)
```

`make_announcement_payload` builds a JSON string; `make_announcement_msg` builds a typed `Announcement` ROS2 message. Both are imported here so callers can access them from a single import. The actual implementation lives in `announcement_contract.py` to avoid a circular dependency with the ROS2 message type.

## What Was Removed

An earlier version of this module had a `handle_intent` method and a `BehaviorResult` dataclass — a full dispatch layer mapping intent names to handler functions. This was removed because it duplicated the `CommandDispatcher` pattern and added a second dispatch mechanism with no clear boundary. Intent handling now flows through `CommandDispatcher` via the intent command group.

## Observations

- **No slot validation.** `parse_intent` validates structure but not slot contents. An intent `{"name": "count_objects", "slots": {}}` (missing `object_type`) will parse successfully and fail later. Schema validation per intent name would catch this earlier.
- **`source` default is "unknown".** The default should probably be required, not silently defaulted, to ensure traceability in logs.
- **Single method class.** `BehaviorManager` has one public method. It could be a module-level function. The class form is kept for future expansion (e.g., intent history, rate limiting).
