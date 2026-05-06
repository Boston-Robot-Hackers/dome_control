---
version: "1.0"
generated: "2026-05-06"
---

# IntentMapper

`intent_mapper.py` is the small translation layer between Vosk transcript text
and normalized intent dictionaries. Its job is not to understand language in a
general sense. It maps a constrained command vocabulary into the robot's
existing intent contract, with the smallest amount of logic needed to keep the
voice path predictable.

## Why This Module Exists

Voice input is already constrained by the recognizer. That makes a full NLU
stack unnecessary here and, more importantly, undesirable. The mapper stays as
plain substring matching so it is easy to reason about, easy to test, and easy
to keep aligned with the wake-word and grammar lists used by the runtime.

```python
VOSK_COMMANDS = json.dumps([
    "go forward", "go backward", "turn left", "turn right",
    "what do you see", "describe the scene", "what do you see around you",
    "look around", "what's there",
    "how many", "count",
    "stop", "halt",
    "start exploring", "explore",
    "be quiet", "quiet",
    "battery", "battery level",
    "where are you", "where",
    "get status", "what's your status", "what's going on",
    "[unk]",
])
```

This list is both documentation and a recognition fence. Anything not in the
list is intentionally out of scope for the voice path. The current set is
trimmed to the intents the robot actually supports from voice.

## Mapping Strategy

```python
PHRASE_INTENTS = (
    (("stop", "halt"), "stop"),
    (("go forward",), "move_forward"),
    (("go backward",), "move_backward"),
    (("turn left",), "turn_left"),
    (("turn right",), "turn_right"),
    (("start exploring", "explore"), "start_exploring"),
    (("be quiet", "quiet"), "be_quiet"),
    (("battery",), "get_battery"),
    (("where are you", "where"), "get_location"),
    (("get status", "what's your status", "what's going on", "status"), "get_status"),
)
```

The mapper is intentionally table-driven. The data structure is the important
part: it makes the accepted phrases obvious, keeps the `map_intent()` body
small, and makes future additions or removals mechanical.

```python
def map_intent(self, text: str) -> dict | None:
    normalized_text = text.lower().strip()
    if not normalized_text or normalized_text == "[unk]":
        return None

    if contains_phrase(normalized_text, DESCRIBE_SCENE_PHRASES):
        return {"name": "describe_scene", "source": self.SOURCE, "slots": {}}

    if contains_phrase(normalized_text, COUNT_OBJECT_PHRASES):
        return make_count_objects_intent(normalized_text, self.SOURCE)

    for phrases, name in PHRASE_INTENTS:
        if contains_phrase(normalized_text, phrases):
            return {"name": name, "source": self.SOURCE, "slots": {}}

    return None
```

The function performs three steps:

1. Normalize the transcript.
2. Check for the semantic query patterns first.
3. Fall back to the command phrase table.

That order matters. A voice command like `count cans` should route into the
object-count path before the generic intent matcher sees the word `count`.

## Object Extraction

`count_objects` is the only intent here that carries a slot.

```python
def make_count_objects_intent(text: str, source: str) -> dict:
    object_type = extract_object(text)
    slots = {"object_type": object_type} if object_type else {}
    return {"name": "count_objects", "source": source, "slots": slots}
```

The extraction step is intentionally simple. It looks for known object words
and fills the slot if one is present. If no object type appears in the
transcript, the intent is still valid and the behavior layer can decide how to
respond.

## Compatibility

```python
DEFAULT_MAPPER = IntentMapper()

def map_intent(text: str) -> dict | None:
    return DEFAULT_MAPPER.map_intent(text)
```

The module-level wrapper keeps the old call sites working while the class-based
API remains the canonical implementation.

## Observations

- The mapper is deliberately conservative. If a phrase is removed from the
  grammar or the intent table, the voice path stops recognizing it instead of
  guessing.
- The current voice contract does not include `go home`, `follow me`, `sleep`,
  or `wake`, so those phrases are intentionally absent from this version.
- The matcher uses substring checks. That is enough for the constrained grammar
  and keeps the implementation easy to audit.
