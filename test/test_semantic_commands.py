#!/usr/bin/env python3
# test_semantic_commands.py — tests for scene command routing
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
# Note: registry-based scene command tests removed in F15/T07.
# scene.describe and scene.count now route via dispatch_text → _BEHAVIOR_COMMANDS.
# See test_command_dispatcher_text.py::TestDispatchTextBehaviorIntents.
import json
from unittest.mock import Mock

import pytest

from dome_control.commands.command_dispatcher import CommandDispatcher
from dome_control.commands.robot_controller import CommandResponse


class TestSceneCommandsViaDispatchText:

    @pytest.fixture
    def setup(self):
        rc = Mock()
        published = []
        from dome_control.commands.intent_publisher import IntentPublisher
        pub = IntentPublisher(publish_fn=published.append)
        dispatcher = CommandDispatcher(rc, intent_publisher=pub)
        return dispatcher, published

    def test_scene_describe_publishes_describe_scene_intent(self, setup):
        dispatcher, published = setup
        result = dispatcher.dispatch_text("scene describe")
        assert result.success is True
        assert json.loads(published[0])["name"] == "describe_scene"

    def test_scene_count_publishes_count_objects_intent(self, setup):
        dispatcher, published = setup
        result = dispatcher.dispatch_text("scene count")
        assert result.success is True
        assert json.loads(published[0])["name"] == "count_objects"

    def test_scene_describe_via_execute(self, setup):
        dispatcher, published = setup
        result = dispatcher.execute("scene.describe", {})
        assert result.success is True
        import json
        assert json.loads(published[0])["name"] == "describe_scene"
