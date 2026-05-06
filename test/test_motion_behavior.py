#!/usr/bin/env python3
# test_motion_behavior.py — tests for MotionBehavior
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from unittest.mock import Mock

from control.behavior_manager import Intent
from control.behaviors.motion_behavior import MotionBehavior


def make_intent(name, slots=None):
    return Intent(name=name, source="test", slots=slots or {})


class TestMotionBehaviorHandles:

    def test_handles_stop(self):
        mb = MotionBehavior(Mock())
        assert mb.handles("stop") is True

    def test_handles_explore(self):
        mb = MotionBehavior(Mock())
        assert mb.handles("explore") is True

    def test_handles_drive_square(self):
        mb = MotionBehavior(Mock())
        assert mb.handles("drive_square") is True

    def test_does_not_handle_describe_scene(self):
        mb = MotionBehavior(Mock())
        assert mb.handles("describe_scene") is False

    def test_does_not_handle_unknown(self):
        mb = MotionBehavior(Mock())
        assert mb.handles("fly_to_moon") is False


class TestMotionBehaviorExecute:

    def test_stop_calls_stop_robot(self):
        rc = Mock()
        mb = MotionBehavior(rc)
        mb.execute(make_intent("stop"))
        rc.stop_robot.assert_called_once_with()

    def test_drive_square_calls_script_square_with_meters(self):
        rc = Mock()
        mb = MotionBehavior(rc)
        mb.execute(make_intent("drive_square", {"meters": "2.5"}))
        rc.script_square.assert_called_once_with(2.5)

    def test_drive_square_defaults_to_1_meter(self):
        rc = Mock()
        mb = MotionBehavior(rc)
        mb.execute(make_intent("drive_square"))
        rc.script_square.assert_called_once_with(1.0)

    def test_explore_does_not_raise(self):
        rc = Mock()
        mb = MotionBehavior(rc)
        mb.execute(make_intent("explore"))  # not yet implemented, must not crash

    def test_unknown_intent_does_nothing(self):
        rc = Mock()
        mb = MotionBehavior(rc)
        mb.execute(make_intent("fly_to_moon"))
        rc.stop_robot.assert_not_called()
        rc.script_square.assert_not_called()
