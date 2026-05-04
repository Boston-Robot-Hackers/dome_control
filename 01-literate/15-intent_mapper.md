---
version: "1.0"
generated: "2026-05-04"
---

# IntentMapper

`intent_mapper.py` converts raw transcription text into structured intent dicts. It is deliberately isolated: no ROS2, no audio, no network — pure string matching. This makes it independently testable.

## Constrained Vocabulary

```python
VOSK_COMMANDS = json.dumps([
    "what do you see", "describe the scene", "what do you see around you",
    "look around", "what's there",
    "how many", "count",
    "stop", "halt",
    "go home", "return home", "come back", "home",
    "start exploring", "explore",
    "follow me", "follow",
    "be quiet", "quiet",
    "go to sleep", "sleep",
    "wake up",
    "battery", "battery level",
    "where are you", "where",
    "get status", "what's your status", "what's going on",
    "[unk]",
])
```

This list is passed to Vosk's `KaldiRecognizer` as the allowed vocabulary. Vosk constrains its beam search to only produce tokens from this list, which dramatically improves recognition accuracy for short command phrases at the cost of rejecting anything not in the list. `[unk]` is the Vosk token for "I heard speech but it matched nothing".

The vocabulary list must stay in sync with the phrases matched in `map_intent`. If a phrase is matched in `map_intent` but not in `VOSK_COMMANDS`, Vosk will never transcribe it.

## Intent Mapping

```python
class IntentMapper:
    def map_intent(self, text: str) -> Optional[dict]:
        t = text.lower().strip()
        if not t or t == "[unk]":
            return None

        if _contains(t, "what do you see", "describe", "what's there", "look around", ...):
            return {"name": "describe_scene", "source": self.SOURCE, "slots": {}}

        if _contains(t, "how many", "count"):
            obj = _extract_object(t)
            return {"name": "count_objects", "source": "voice",
                    "slots": {"object_type": obj} if obj else {}}
        ...
        return None
```

The mapping is a sequence of `if _contains(...)` checks — no fancy NLU, no regex, just substring matching on lowercased text. This is appropriate for constrained-vocabulary voice commands where the recogniser already ensures the text is one of a small set of phrases.

`None` return means "no recognisable intent" — the caller (`VoiceInputNode`) responds with "say again."

## Object Extraction

```python
OBJECT_TYPES = ["can", "bottle", "person", "chair", "table", "ball", "cup", "box"]

def _extract_object(text: str) -> Optional[str]:
    for obj in OBJECT_TYPES:
        if obj in text:
            return obj
    return None
```

For `count_objects`, the mapper tries to extract what type of object to count from the transcript. "How many chairs" → `slots: {object_type: "chair"}`. If no object type is found, `slots` is empty and the behavior manager must decide how to handle the underspecified intent.

## Module-Level Compatibility Wrapper

```python
_DEFAULT_MAPPER = IntentMapper()

def map_intent(text: str) -> Optional[dict]:
    """Compatibility wrapper for existing call sites and tests."""
    return _DEFAULT_MAPPER.map_intent(text)
```

A module-level `map_intent` function wraps the class for callers that imported the old functional API before `IntentMapper` was introduced as a class.

## Observations

- `_contains` matches substrings, so "quiet" would match inside "not quiet". For the constrained Vosk vocabulary this isn't a problem in practice, but it's a subtle correctness issue if vocabulary expands.
- Intents like `return_home`, `start_exploring`, `follow_me`, `sleep`, `wake`, `get_battery`, `get_location`, `get_status` are mapped but `BehaviorManager.handle_intent` only handles `describe_scene`. All others silently log "Unsupported intent."
- Adding new intents requires changes in three places: `VOSK_COMMANDS` vocabulary, `map_intent` matching, and `BehaviorManager.handle_intent` handling.
