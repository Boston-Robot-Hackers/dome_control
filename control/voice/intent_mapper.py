#!/usr/bin/env python3
"""
intent_mapper.py — maps Vosk transcripts to structured intent dicts.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import json

OBJECT_TYPES = ["can", "bottle", "person", "chair", "table", "ball", "cup", "box"]

DESCRIBE_SCENE_PHRASES = (
    "what do you see",
    "describe",
    "what's there",
    "look around",
    "what do you see around",
)

COUNT_OBJECT_PHRASES = ("how many", "count")

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

# Vosk constrained vocabulary — must cover every phrase matched in map_intent()
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


def contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


class IntentMapper:
    """Keyword/phrase matcher from transcript text to normalized voice intents."""

    SOURCE = "voice"

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


DEFAULT_MAPPER = IntentMapper()


def map_intent(text: str) -> dict | None:
    """Compatibility wrapper for existing call sites and tests."""
    return DEFAULT_MAPPER.map_intent(text)


def make_count_objects_intent(text: str, source: str) -> dict:
    object_type = extract_object(text)
    slots = {"object_type": object_type} if object_type else {}
    return {"name": "count_objects", "source": source, "slots": slots}


def extract_object(text: str) -> str | None:
    for object_type in OBJECT_TYPES:
        if object_type in text:
            return object_type
    return None
