#!/usr/bin/env python3
# motion_behavior.py — motion intent handler
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Handles motion-domain intents. No ROS2 dependency."""

from control.behavior_manager import Intent

MOTION_INTENTS = {"stop", "explore", "drive_square"}


class MotionBehavior:
    """Executes motion intents via RobotController."""

    def __init__(self, robot_controller):
        self.rc = robot_controller

    def handles(self, intent_name: str) -> bool:
        return intent_name in MOTION_INTENTS

    def execute(self, intent: Intent, node=None) -> None:
        if intent.name == "stop":
            self.rc.stop_robot()
        elif intent.name == "drive_square":
            meters = float(intent.slots.get("meters", 1.0))
            self.rc.script_square(meters)
        elif intent.name == "explore":
            pass  # not yet implemented
