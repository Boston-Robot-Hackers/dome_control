#!/usr/bin/env python3
# describe_scene_stub_node.py — temporary describe-scene service
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Temporary describe-scene service for behavior-manager smoke tests."""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class DescribeSceneStubNode(Node):
    def __init__(self):
        super().__init__("describe_scene_stub")
        self.service = self.create_service(
            Trigger, "/describe_scene", self.describe_scene
        )

    def describe_scene(self, request, response):
        response.success = True
        response.message = "I see 2 cups and 1 can"
        return response


def main():
    rclpy.init()
    node = DescribeSceneStubNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
