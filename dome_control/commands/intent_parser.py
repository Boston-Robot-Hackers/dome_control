#!/usr/bin/env python3
# intent_parser.py — pure intent parsing logic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Pure intent parser — no ROS2 dependency."""

import json
from dataclasses import dataclass

from dome_control.announcement_contract import (
    make_announcement_msg,
    make_announcement_payload,
)

__all__ = [
    'IntentParser',
    'Intent',
    'make_announcement_msg',
    'make_announcement_payload',
]


@dataclass
class Intent:
    name: str
    source: str
    slots: dict


class IntentParser:
    """Parse raw intent JSON into Intent dataclass. No ROS2 dependency."""

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
        if not isinstance(source, str) or not source:
            raise ValueError("Intent field 'source' must be a non-empty string")

        slots = raw.get("slots", {})
        if not isinstance(slots, dict):
            raise ValueError("Intent field 'slots' must be an object")

        return Intent(name=name, source=source, slots=slots)
