---
version: "1.0"
generated: "2026-05-12"
---

# SpeechApi — Announcement Publisher

## Purpose

`SpeechApi` is the CLI-side ROS2 node for publishing speech to the `/announcement` topic. It wraps `Announcement` dataclass construction and publishing into a single `speak()` call, giving `RobotController` a clean interface for text output without touching ROS2 message types directly.

## Design

`SpeechApi` extends `BaseApi` (the shared ROS2 node base class). Like all API classes, it is instantiated lazily by `RobotController` on first use:

```python
@property
def speech(self) -> SpeechApi:
    if self.speech_node is None:
        self.speech_node = SpeechApi(self.config)
    return self.speech_node
```

The publisher is created in `__init__` but `AnnouncementMsg` is imported lazily inside `__init__` to avoid pulling in ROS2 message types at module load:

```python
    def __init__(self, config_manager: cm.ConfigManager = None):
        super().__init__("speech_api", config_manager)
        from dome_control.announcement_contract import AnnouncementMsg
        self.announcement_pub = self.create_publisher(AnnouncementMsg, "/announcement", 10)
```

## The speak() Method

```python
    def speak(self, text: str, priority: int = PRIORITY_CHITCHAT) -> None:
        ann = Announcement(text=text, priority=priority, source="cli")
        self.announcement_pub.publish(ann.to_msg())
        self.log_info(f"Speak published: {text!r}")
```

`source="cli"` tags all CLI-originated speech. Priority defaults to `PRIORITY_CHITCHAT` — the lowest tier, meaning `SpeechOutputNode` may defer or drop it if higher-priority messages are queued.

## Observations

- Thin wrapper with one method. Could be a free function if `BaseApi` weren't needed for the publisher lifecycle.
- `source` is hardcoded to `"cli"`. If other non-node callers use this class, the source tag would be wrong.
- `PRIORITY_CHITCHAT` default means CLI speech can be preempted by robot-generated announcements. This is intentional — robot operational messages take precedence.
