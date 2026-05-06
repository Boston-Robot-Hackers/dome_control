#!/usr/bin/env python3
# test_behavior_manager_node_routing.py — routing tests for BehaviorManagerNode
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
# Test tier: No-ROS (fake ROS2 injected via conftest.py)
import json
from unittest.mock import Mock

import pytest

from control.commands.intent_parser import IntentParser
from control.nodes.behavior_manager_node import BehaviorManagerNode


def make_string_msg(data: str):
    msg = Mock()
    msg.data = data
    return msg


def make_intent_json(name, source="test", slots=None):
    return json.dumps({"name": name, "source": source, "slots": slots or {}})


@pytest.fixture
def node():
    n = BehaviorManagerNode.__new__(BehaviorManagerNode)
    n.parser = IntentParser()
    n.get_logger = Mock(return_value=Mock())

    motion = Mock()
    perception = Mock()
    motion.handles.side_effect = lambda name: name in {"stop", "explore", "drive_square"}
    perception.handles.side_effect = lambda name: name in {"describe_scene", "count_objects"}

    n.handlers = [motion, perception]
    return n, motion, perception


class TestBehaviorManagerNodeRouting:

    def test_stop_routes_to_motion_handler(self, node):
        n, motion, perception = node
        n.on_intent(make_string_msg(make_intent_json("stop")))
        motion.execute.assert_called_once()
        perception.execute.assert_not_called()

    def test_describe_scene_routes_to_perception_handler(self, node):
        n, motion, perception = node
        n.on_intent(make_string_msg(make_intent_json("describe_scene")))
        perception.execute.assert_called_once()
        motion.execute.assert_not_called()

    def test_unknown_intent_logs_warning(self, node):
        n, motion, perception = node
        n.on_intent(make_string_msg(make_intent_json("fly_to_moon")))
        motion.execute.assert_not_called()
        perception.execute.assert_not_called()
        n.get_logger().warn.assert_called_once()

    def test_malformed_json_logs_warning_no_crash(self, node):
        n, motion, perception = node
        n.on_intent(make_string_msg("{bad json"))
        motion.execute.assert_not_called()
        perception.execute.assert_not_called()
        n.get_logger().warn.assert_called_once()

    def test_explore_routes_to_motion_handler(self, node):
        n, motion, perception = node
        n.on_intent(make_string_msg(make_intent_json("explore")))
        motion.execute.assert_called_once()
        perception.execute.assert_not_called()
