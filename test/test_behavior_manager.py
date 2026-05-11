#!/usr/bin/env python3
# test_behavior_manager.py — tests for IntentParser
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
import json

import pytest

from dome_control.commands.intent_parser import (
    IntentParser,
    make_announcement_msg,
    make_announcement_payload,
)
from dome_control.announcement_contract import PRIORITY_QUERY_REPLY


class TestIntentParser:

    def test_parse_intent_json(self):
        manager = IntentParser()

        intent = manager.parse_intent(
            '{"name": "describe_scene", "source": "cli", "slots": {}}'
        )

        assert intent.name == "describe_scene"
        assert intent.source == "cli"
        assert intent.slots == {}

    def test_parse_rejects_invalid_json(self):
        manager = IntentParser()

        with pytest.raises(ValueError, match="Invalid intent JSON"):
            manager.parse_intent("{")

    def test_parse_rejects_missing_name(self):
        manager = IntentParser()

        with pytest.raises(ValueError, match="name"):
            manager.parse_intent('{"source": "cli", "slots": {}}')

    def test_parse_rejects_non_object_slots(self):
        manager = IntentParser()

        with pytest.raises(ValueError, match="slots"):
            manager.parse_intent(
                '{"name": "describe_scene", "source": "cli", "slots": []}'
            )

    def test_make_announcement_payload(self):
        payload = make_announcement_payload("I see a can")

        data = json.loads(payload)
        assert data["text"] == "I see a can"
        assert data["priority"] == PRIORITY_QUERY_REPLY
        assert data["source"] == "behavior_manager"

    def test_make_announcement_msg(self):
        msg = make_announcement_msg("I see a can")

        assert msg.text == "I see a can"
        assert msg.priority == PRIORITY_QUERY_REPLY
        assert msg.source == "behavior_manager"
        assert msg.dedup_key == ""
