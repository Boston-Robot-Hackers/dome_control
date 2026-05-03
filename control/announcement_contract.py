#!/usr/bin/env python3
"""Shared announcement contract for /announcement messages."""

import json
from dataclasses import dataclass

try:
    from builtin_interfaces.msg import Time
except ImportError:
    @dataclass
    class Time:
        sec: int = 0
        nanosec: int = 0


PRIORITY_SAFETY = 0
PRIORITY_STATUS = 1
PRIORITY_QUERY_REPLY = 2
PRIORITY_ACTION_ACK = 3
PRIORITY_DISCOVERY = 4
PRIORITY_CHITCHAT = 5

try:
    from control.msg import Announcement as AnnouncementMsg
except ImportError:
    class AnnouncementMsg:
        PRIORITY_SAFETY = PRIORITY_SAFETY
        PRIORITY_STATUS = PRIORITY_STATUS
        PRIORITY_QUERY_REPLY = PRIORITY_QUERY_REPLY
        PRIORITY_ACTION_ACK = PRIORITY_ACTION_ACK
        PRIORITY_DISCOVERY = PRIORITY_DISCOVERY
        PRIORITY_CHITCHAT = PRIORITY_CHITCHAT

        def __init__(self):
            self.text = ""
            self.priority = PRIORITY_CHITCHAT
            self.stamp = Time()
            self.source = "unknown"
            self.dedup_key = ""


@dataclass(frozen=True)
class Announcement:
    text: str
    priority: int = PRIORITY_CHITCHAT
    stamp: Time | None = None
    source: str = "unknown"
    dedup_key: str = ""

    def to_payload(self) -> str:
        return json.dumps(
            {
                "text": self.text,
                "priority": self.priority,
                "source": self.source,
                "dedup_key": self.dedup_key,
            }
        )

    def to_msg(self) -> AnnouncementMsg:
        msg = AnnouncementMsg()
        msg.text = self.text
        msg.priority = self.priority
        msg.stamp = self.stamp if self.stamp is not None else Time()
        msg.source = self.source
        msg.dedup_key = self.dedup_key
        return msg

    @classmethod
    def from_payload(cls, payload: str) -> "Announcement":
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError:
            text = payload.strip()
            return cls(text=text) if text else cls(text="")

        if not isinstance(raw, dict):
            return cls(text=str(raw))

        text = raw.get("text", "")
        priority = raw.get("priority", PRIORITY_CHITCHAT)
        source = raw.get("source", "unknown")
        dedup_key = raw.get("dedup_key", "")

        if not isinstance(text, str):
            text = str(text)
        if not isinstance(priority, int):
            try:
                priority = int(priority)
            except (TypeError, ValueError):
                priority = PRIORITY_CHITCHAT
        if not isinstance(source, str):
            source = str(source)
        if not isinstance(dedup_key, str):
            dedup_key = str(dedup_key)

        return cls(
            text=text.strip(),
            priority=priority,
            source=source,
            dedup_key=dedup_key,
        )

    @classmethod
    def from_msg(cls, msg) -> "Announcement":
        if hasattr(msg, "data"):
            return cls.from_payload(msg.data)

        return cls(
            text=str(getattr(msg, "text", "")).strip(),
            priority=int(getattr(msg, "priority", PRIORITY_CHITCHAT)),
            stamp=getattr(msg, "stamp", None),
            source=str(getattr(msg, "source", "unknown")),
            dedup_key=str(getattr(msg, "dedup_key", "")),
        )


def make_announcement_payload(
    text: str,
    *,
    priority: int = PRIORITY_QUERY_REPLY,
    source: str = "behavior_manager",
    dedup_key: str = "",
) -> str:
    return Announcement(
        text=text,
        priority=priority,
        source=source,
        dedup_key=dedup_key,
    ).to_payload()


def make_announcement_msg(
    text: str,
    *,
    priority: int = PRIORITY_QUERY_REPLY,
    source: str = "behavior_manager",
    dedup_key: str = "",
    stamp: Time | None = None,
) -> AnnouncementMsg:
    return Announcement(
        text=text,
        priority=priority,
        stamp=stamp,
        source=source,
        dedup_key=dedup_key,
    ).to_msg()
