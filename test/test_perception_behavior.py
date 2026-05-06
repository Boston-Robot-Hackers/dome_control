#!/usr/bin/env python3
# test_perception_behavior.py — tests for PerceptionBehavior
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from unittest.mock import Mock

import pytest

from control.behavior_manager import Intent
from control.behaviors.perception_behavior import PerceptionBehavior


def make_intent(name, slots=None):
    return Intent(name=name, source="test", slots=slots or {})


def make_mock_node(service_ready=True):
    node = Mock()
    node.describe_scene_client.service_is_ready.return_value = service_ready
    node.get_logger.return_value = Mock()
    return node


class TestPerceptionBehaviorHandles:

    def test_handles_describe_scene(self):
        pb = PerceptionBehavior(Mock())
        assert pb.handles("describe_scene") is True

    def test_handles_count_objects(self):
        pb = PerceptionBehavior(Mock())
        assert pb.handles("count_objects") is True

    def test_does_not_handle_stop(self):
        pb = PerceptionBehavior(Mock())
        assert pb.handles("stop") is False

    def test_does_not_handle_unknown(self):
        pb = PerceptionBehavior(Mock())
        assert pb.handles("fly_to_moon") is False


class TestPerceptionBehaviorExecute:

    def test_describe_scene_calls_service_when_ready(self):
        node = make_mock_node(service_ready=True)
        future = Mock()
        node.describe_scene_client.call_async.return_value = future

        pb = PerceptionBehavior(node)
        pb.execute(make_intent("describe_scene"))

        node.describe_scene_client.call_async.assert_called_once()
        future.add_done_callback.assert_called_once_with(pb.on_describe_scene_done)

    def test_describe_scene_warns_when_service_not_ready(self):
        node = make_mock_node(service_ready=False)

        pb = PerceptionBehavior(node)
        pb.execute(make_intent("describe_scene"))

        node.describe_scene_client.call_async.assert_not_called()
        node.get_logger().warn.assert_called_once()

    def test_count_objects_logs_unimplemented(self):
        node = make_mock_node()

        pb = PerceptionBehavior(node)
        pb.execute(make_intent("count_objects"))

        node.get_logger().warn.assert_called_once()

    def test_unknown_intent_does_nothing(self):
        node = make_mock_node()

        pb = PerceptionBehavior(node)
        pb.execute(make_intent("fly_to_moon"))

        node.describe_scene_client.call_async.assert_not_called()


class TestPerceptionBehaviorCallbacks:

    def test_on_done_publishes_announcement_on_success(self):
        node = make_mock_node()
        response = Mock()
        response.success = True
        response.message = "I see a chair"
        future = Mock()
        future.result.return_value = response

        pb = PerceptionBehavior(node)
        pb.on_describe_scene_done(future)

        node.announcement_pub.publish.assert_called_once()
        node.get_logger().info.assert_called_with("I see a chair")

    def test_on_done_warns_on_failure_response(self):
        node = make_mock_node()
        response = Mock()
        response.success = False
        response.message = "no scene"
        future = Mock()
        future.result.return_value = response

        pb = PerceptionBehavior(node)
        pb.on_describe_scene_done(future)

        node.announcement_pub.publish.assert_not_called()
        node.get_logger().warn.assert_called_once()

    def test_on_done_logs_error_on_exception(self):
        node = make_mock_node()
        future = Mock()
        future.result.side_effect = RuntimeError("timeout")

        pb = PerceptionBehavior(node)
        pb.on_describe_scene_done(future)

        node.announcement_pub.publish.assert_not_called()
        node.get_logger().error.assert_called_once()
