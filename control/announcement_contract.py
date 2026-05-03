#!/usr/bin/env python3
"""Shared announcement contract for /announcement payloads."""

import json
from dataclasses import dataclass


PRIORITY_SAFETY = 0
PRIORITY_STATUS = 1
PRIORITY_QUERY_REPLY = 2
PRIORITY_ACTION_ACK = 3
PRIORITY_DISCOVERY = 4
PRIORITY_CHITCHAT = 5


@dataclass(frozen=True)
class Announcement:
    text: str
    priority: int = PRIORITY_CHITCHAT
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
