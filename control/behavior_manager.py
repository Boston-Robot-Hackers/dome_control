#!/usr/bin/env python3
# behavior_manager.py — pure intent dispatch logic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Pure behavior-manager logic for intent dispatch."""

import json
from collections.abc import Callable
from dataclasses import dataclass

from control.announcement_contract import make_announcement_payload

__all__ = [
    'BehaviorManager',
    'BehaviorResult',
    'Intent',
    'make_announcement_payload',
]


@dataclass
class Intent:
    name: str
    source: str
    slots: dict


@dataclass
class BehaviorResult:
    handled: bool
    message: str
    announcement: str | None = None


class BehaviorManager:
    """Dispatch normalized intents without depending on ROS2."""

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

    def handle_intent(
        self,
        intent: Intent,
        describe_scene: Callable[[], str],
        announce: Callable[[str], None],
    ) -> BehaviorResult:
        if intent.name == "describe_scene":
            summary = describe_scene()
            announce(summary)
            return BehaviorResult(True, "describe_scene handled", summary)

        return BehaviorResult(False, f"Unsupported intent: {intent.name}")
