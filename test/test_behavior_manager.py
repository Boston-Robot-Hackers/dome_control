#!/usr/bin/env python3
# test_behavior_manager.py — tests for pure behavior-manager logic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
import json

import pytest

from control.behavior_manager import (
    BehaviorManager,
    make_announcement_msg,
    make_announcement_payload,
)
from control.announcement_contract import PRIORITY_QUERY_REPLY


class TestBehaviorManager:

    def test_parse_intent_json(self):
        manager = BehaviorManager()

        intent = manager.parse_intent(
            '{"name": "describe_scene", "source": "cli", "slots": {}}'
        )

        assert intent.name == "describe_scene"
        assert intent.source == "cli"
        assert intent.slots == {}

    def test_parse_rejects_invalid_json(self):
        manager = BehaviorManager()

        with pytest.raises(ValueError, match="Invalid intent JSON"):
            manager.parse_intent("{")

    def test_parse_rejects_missing_name(self):
        manager = BehaviorManager()

        with pytest.raises(ValueError, match="name"):
            manager.parse_intent('{"source": "cli", "slots": {}}')

    def test_parse_rejects_non_object_slots(self):
        manager = BehaviorManager()

        with pytest.raises(ValueError, match="slots"):
            manager.parse_intent(
                '{"name": "describe_scene", "source": "cli", "slots": []}'
            )

    def test_handle_describe_scene_announces_summary(self):
        manager = BehaviorManager()
        intent = manager.parse_intent(
            '{"name": "describe_scene", "source": "cli", "slots": {}}'
        )
        announcements = []

        result = manager.handle_intent(
            intent,
            describe_scene=lambda: "I see 2 cups and 1 can",
            announce=announcements.append,
        )

        assert result.handled is True
        assert result.announcement == "I see 2 cups and 1 can"
        assert announcements == ["I see 2 cups and 1 can"]

    def test_handle_unsupported_intent_does_not_announce(self):
        manager = BehaviorManager()
        intent = manager.parse_intent(
            '{"name": "start_exploring", "source": "cli", "slots": {}}'
        )
        announcements = []

        result = manager.handle_intent(
            intent,
            describe_scene=lambda: "unused",
            announce=announcements.append,
        )

        assert result.handled is False
        assert "Unsupported intent" in result.message
        assert announcements == []

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
