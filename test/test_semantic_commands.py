#!/usr/bin/env python3
# test_semantic_commands.py — tests for scene command aliases
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from unittest.mock import MagicMock

import pytest

from control.commands.command_dispatcher import CommandDispatcher
from control.commands.robot_controller import CommandResponse, RobotController


class TestSemanticCommands:

    @pytest.fixture
    def mock_rc(self):
        mock = MagicMock(spec=RobotController)
        mock.publish_intent_describe_scene.return_value = CommandResponse(
            True, "Intent published: describe_scene"
        )
        mock.publish_intent_count_objects.return_value = CommandResponse(
            True, "Intent published: count_objects"
        )
        return mock

    @pytest.fixture
    def dispatcher(self, mock_rc):
        return CommandDispatcher(mock_rc)

    def test_scene_describe_dispatches_describe_scene_intent(self, dispatcher, mock_rc):
        result = dispatcher.execute("scene.describe", {})

        assert result.success is True
        mock_rc.publish_intent_describe_scene.assert_called_once_with()

    def test_scene_count_dispatches_count_objects_intent(self, dispatcher, mock_rc):
        result = dispatcher.execute("scene.count", {"object_type": "can"})

        assert result.success is True
        mock_rc.publish_intent_count_objects.assert_called_once_with(object_type="can")

    def test_scene_count_requires_object_type(self, dispatcher):
        result = dispatcher.execute("scene.count", {})

        assert result.success is False
        assert "object_type" in result.message

    def test_scene_commands_in_registry(self, dispatcher):
        cmds = dispatcher.list_commands(group="scene")

        assert "scene.describe" in cmds
        assert "scene.count" in cmds
