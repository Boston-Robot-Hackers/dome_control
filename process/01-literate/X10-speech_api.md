---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X10 — SpeechApi

`ros2_api/speech_api.py` publishes a typed `Announcement` on
`/announcement`, which `dome_voice` speaks. It backs `robot speak <text>`:

```python
def speak(self, text: str, priority: int = PRIORITY_CHITCHAT) -> None:
    ann = Announcement(text=text, priority=priority, source="cli")
    self.announcement_pub.publish(ann.to_msg())
```

## Observations

- **There is a redundant import.** `AnnouncementMsg` is imported inside
  `__init__` even though the module already imports from
  `announcement_contract` at the top. Move it up.
- **Nothing confirms delivery.** The controller sleeps 0.5 s after
  creating this node so the first message isn't lost to discovery. A
  transient-local QoS, or waiting until `get_subscription_count() > 0`,
  would be deterministic.
- **Spoken text can be taken as a query reply.** See X06 and
  `08-intent_api.md`.
