#!/usr/bin/env python3
"""Maps Vosk transcript text to structured intent dicts. No ROS2, no audio."""

import json
from typing import Optional

OBJECT_TYPES = ["can", "bottle", "person", "chair", "table", "ball", "cup", "box"]

# Vosk constrained vocabulary — must cover every phrase matched in map_intent()
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


def _contains(text: str, *phrases: str) -> bool:
    return any(p in text for p in phrases)


def map_intent(text: str) -> Optional[dict]:
    """Return intent dict or None if text does not match any known command."""
    t = text.lower().strip()
    if not t or t == "[unk]":
        return None

    if _contains(t, "what do you see", "describe", "what's there", "look around",
                 "what do you see around"):
        return {"name": "describe_scene", "source": "voice", "slots": {}}

    if _contains(t, "how many", "count"):
        obj = _extract_object(t)
        return {"name": "count_objects", "source": "voice",
                "slots": {"object_type": obj} if obj else {}}

    if _contains(t, "stop", "halt"):
        return {"name": "stop", "source": "voice", "slots": {}}

    if _contains(t, "go home", "return home", "come back", "home"):
        return {"name": "return_home", "source": "voice", "slots": {}}

    if _contains(t, "start exploring", "explore"):
        return {"name": "start_exploring", "source": "voice", "slots": {}}

    if _contains(t, "follow me", "follow"):
        return {"name": "follow_me", "source": "voice", "slots": {}}

    if _contains(t, "be quiet", "quiet"):
        return {"name": "be_quiet", "source": "voice", "slots": {}}

    if _contains(t, "go to sleep", "sleep"):
        return {"name": "sleep", "source": "voice", "slots": {}}

    if _contains(t, "wake up"):
        return {"name": "wake", "source": "voice", "slots": {}}

    if _contains(t, "battery"):
        return {"name": "get_battery", "source": "voice", "slots": {}}

    if _contains(t, "where are you", "where"):
        return {"name": "get_location", "source": "voice", "slots": {}}

    if _contains(t, "get status", "what's your status", "what's going on", "status"):
        return {"name": "get_status", "source": "voice", "slots": {}}

    return None


def _extract_object(text: str) -> Optional[str]:
    for obj in OBJECT_TYPES:
        if obj in text:
            return obj
    return None
