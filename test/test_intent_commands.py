#!/usr/bin/env python3
# test_intent_commands.py — tests for IntentApi (low-level ROS2 publisher)
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
# Note: TestIntentCommands (registry-based dispatch) removed in F15/T07.
# Intent commands now route via dispatch_text → _BEHAVIOR_COMMANDS → IntentPublisher.
# See test_command_dispatcher_text.py::TestDispatchTextBehaviorIntents.
import json
from unittest.mock import MagicMock

import pytest


class TestIntentApi:

    def _make_intent_api(self):
        import control.ros2_api.intent_api as ia
        api = ia.IntentApi.__new__(ia.IntentApi)
        api.intent_pub = MagicMock()
        api.log_info = MagicMock()
        return api

    def test_publish_serializes_json(self):
        import control.ros2_api.intent_api as ia
        api = self._make_intent_api()
        ia.IntentApi.publish(api, "stop", "cli", {})

        api.intent_pub.publish.assert_called_once()
        msg = api.intent_pub.publish.call_args[0][0]
        data = json.loads(msg.data)
        assert data["name"] == "stop"
        assert data["source"] == "cli"
        assert data["slots"] == {}

    def test_publish_includes_slots(self):
        import control.ros2_api.intent_api as ia
        api = self._make_intent_api()
        ia.IntentApi.publish(api, "count_objects", "cli", {"object_type": "chair"})

        msg = api.intent_pub.publish.call_args[0][0]
        data = json.loads(msg.data)
        assert data["slots"] == {"object_type": "chair"}
