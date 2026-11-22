---
version: "1.0"
generated: "2026-11-22"
---

# IntentParser — validating `/intent` at the boundary

`intent_parser.py` turns the JSON string carried on `/intent` into a typed
`Intent`. It is the single validation boundary for intents: everything
downstream (`MotionBehavior`, `PerceptionBehavior`) trusts what it is
given.

It has no ROS imports, so it unit-tests in isolation.

## The wire format

An intent on `/intent` is a `std_msgs/String` whose `data` is a JSON object:

```json
{"name": "describe_scene", "source": "voice", "slots": {}}
```

- **`name`**: the intent name. Each name is owned by exactly one package
  (F19): motion and perception names belong here, and mission names belong
  to `dome_mission`.
- **`source`**: who sent it (`cli`, `voice`, …). It is used for logging
  only.
- **`slots`**: named arguments, for example `{"meters": 1.0}` or
  `{"label": "cup"}`.

## Strict, with one message per failure

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
    ...
    return Intent(name=name, source=source, slots=slots)
```

Every failure is a `ValueError` with a specific message. The caller,
`BehaviorManagerNode.on_intent`, logs it as a warning and drops the intent.
This is the style guide's *validate once at the boundary* rule applied
properly: unlike the announcement contract, nothing is coerced or repaired.

Note one asymmetry: `source` defaults to `"unknown"` when absent, but an
explicitly empty string is rejected.

## A re-export that leaks

The module also re-exports the two announcement helpers:

```python
from dome_control.announcement_contract import (
    make_announcement_msg,
    make_announcement_payload,
)
__all__ = ["Intent", "IntentParser", "make_announcement_msg", ...]
```

`PerceptionBehavior` imports `make_announcement_msg` from here, while
`MotionBehavior` imports it from `announcement_contract`. That is two paths
to the same function, and a parser module that also exports output helpers.

## Observations

1. **Drop the announcement re-export.** Have `PerceptionBehavior` import
   from `announcement_contract` like everyone else, so this module is only
   about parsing.
2. **Slots are not validated.** `slots` is checked to be a dict, but each
   handler then coerces its own values (`float(intent.slots.get("meters",
   1.0))`). A bad `meters` raises inside a ROS callback instead of at this
   boundary. A per-intent slot schema would fix that.
3. **`IntentParser` is a class with one stateless method.** A module-level
   `parse_intent()` function would say the same thing with less code.
4. **There is no registry of known intent names.** An intent nobody owns
   only shows up later as "Unhandled intent" in the behavior manager log,
   and the voice side, the CLI and the handlers each keep their own name
   lists (issue I08).
