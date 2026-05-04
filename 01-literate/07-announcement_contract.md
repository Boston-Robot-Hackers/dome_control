---
version: "1.0"
generated: "2026-05-04"
---

# Announcement Contract

`announcement_contract.py` defines the shared data model for messages published to the `/announcement` topic. It is the contract between producers (behavior manager, voice input) and consumers (speech output node).

## Why a Separate Contract Module

Multiple nodes in different files need to agree on the `/announcement` message structure. A shared module avoids each node reimplementing its own serialization logic and prevents the producer and consumer from drifting apart.

## Priority Constants

The module establishes an ordered urgency scale:

```python
PRIORITY_SAFETY = 0        # highest — obstacle, emergency
PRIORITY_STATUS = 1        # battery low, localization lost
PRIORITY_QUERY_REPLY = 2   # answer to a user question
PRIORITY_ACTION_ACK = 3    # "turning left"
PRIORITY_DISCOVERY = 4     # "I see a chair"
PRIORITY_CHITCHAT = 5      # lowest — greetings, idle commentary
```

Lower numbers = higher priority. The scale is not yet enforced by a priority queue in the speech output node, but is the intended semantic for future queueing logic.

## Dual Import Strategy

The module uses `try/except ImportError` in two places to allow use outside a ROS2 environment:

```python
try:
    from builtin_interfaces.msg import Time
except ImportError:
    @dataclass
    class Time:
        sec: int = 0
        nanosec: int = 0
```

And similarly for `AnnouncementMsg`. This lets unit tests import the module without a ROS2 installation. The stub classes provide just enough structure for pure-Python assertions.

## The `Announcement` Dataclass

```python
@dataclass(frozen=True)
class Announcement:
    text: str
    priority: int = PRIORITY_CHITCHAT
    stamp: Time | None = None
    source: str = "unknown"
    dedup_key: str = ""
```

`frozen=True` makes instances hashable and immutable — safe to pass across ROS2 callbacks.

`dedup_key` is a forward-looking field intended for suppressing repeated identical announcements (e.g., a "battery low" warning that would otherwise fire every few seconds).

## Serialization Paths

```
Producer                               Consumer
────────                               ────────
Announcement
  → to_payload() → JSON string  ←→  from_payload() → Announcement
  → to_msg() → AnnouncementMsg  ←→  from_msg()     → Announcement
```

`to_payload` / `from_payload` use a plain JSON string over `std_msgs/String`. This allows nodes that don't have the custom message type compiled to still participate via the JSON path.

`from_payload` is defensive: if the payload is not valid JSON, the whole string is treated as the announcement text. This lets legacy publishers still work.

## Factory Helpers

```python
def make_announcement_payload(text, *, priority, source, dedup_key) -> str
def make_announcement_msg(text, *, priority, source, dedup_key, stamp) -> AnnouncementMsg
```

Convenience wrappers so call sites don't need to construct `Announcement` and immediately call `.to_payload()` or `.to_msg()`.

## Observations

- The `dedup_key` field is defined but nothing currently populates it with meaningful values. The speech output node does not suppress duplicates.
- Priority is not acted on anywhere. A future priority queue in `SpeechOutputNode` would need to buffer incoming announcements and sort by priority before speaking.
