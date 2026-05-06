#!/usr/bin/env python3
# behavior_manager_node.py — ROS2 shell for behavior manager
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""ROS2 node that receives intents and routes to domain behavior handlers."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from control.announcement_contract import AnnouncementMsg
from control.behavior_manager import IntentParser
from control.behaviors.motion_behavior import MotionBehavior
from control.behaviors.perception_behavior import PerceptionBehavior
from control.commands.config_manager import ConfigManager
from control.commands.robot_controller import RobotController


class BehaviorManagerNode(Node):
    def __init__(self):
        super().__init__("behavior_manager")
        self.parser = IntentParser()

        rc = RobotController(ConfigManager())
        self.handlers = [
            MotionBehavior(rc),
            PerceptionBehavior(self),
        ]

        self.intent_sub = self.create_subscription(
            String, "/intent", self.on_intent, 10
        )
        self.announcement_pub = self.create_publisher(
            AnnouncementMsg, "/announcement", 10
        )
        self.describe_scene_client = self.create_client(Trigger, "/describe_scene")

    def on_intent(self, msg: String) -> None:
        try:
            intent = self.parser.parse_intent(msg.data)
        except ValueError as exc:
            self.get_logger().warn(str(exc))
            return

        for handler in self.handlers:
            if handler.handles(intent.name):
                handler.execute(intent, self)
                return

        self.get_logger().warn(f"Unhandled intent: {intent.name}")


def main():
    rclpy.init()
    node = BehaviorManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
