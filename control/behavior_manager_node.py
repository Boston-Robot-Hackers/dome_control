#!/usr/bin/env python3
# behavior_manager_node.py — ROS2 shell for behavior manager
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""ROS2 node that receives intents and dispatches behavior-manager actions."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from control.behavior_manager import BehaviorManager, make_announcement_payload


class BehaviorManagerNode(Node):
    def __init__(self):
        super().__init__("behavior_manager")
        self.manager = BehaviorManager()
        self.intent_sub = self.create_subscription(
            String, "/intent", self.on_intent, 10
        )
        self.announcement_pub = self.create_publisher(String, "/announcement", 10)
        self.describe_scene_client = self.create_client(Trigger, "/describe_scene")

    def on_intent(self, msg: String) -> None:
        try:
            intent = self.manager.parse_intent(msg.data)
        except ValueError as exc:
            self.get_logger().warn(str(exc))
            return

        if intent.name == "describe_scene":
            self.call_describe_scene()
            return

        self.get_logger().info(f"Unsupported intent received: {intent.name}")

    def call_describe_scene(self) -> None:
        if not self.describe_scene_client.service_is_ready():
            self.get_logger().warn("/describe_scene service is not available")
            return

        future = self.describe_scene_client.call_async(Trigger.Request())
        future.add_done_callback(self.on_describe_scene_done)

    def on_describe_scene_done(self, future) -> None:
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().error(f"/describe_scene call failed: {exc}")
            return

        if not response.success:
            self.get_logger().warn(
                f"/describe_scene returned failure: {response.message}"
            )
            return

        self.publish_announcement(response.message)

    def publish_announcement(self, text: str) -> None:
        msg = String()
        msg.data = make_announcement_payload(text)
        self.announcement_pub.publish(msg)
        self.get_logger().info(text)


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
