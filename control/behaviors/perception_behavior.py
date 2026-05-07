#!/usr/bin/env python3
# perception_behavior.py — perception intent handler
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Handles perception-domain intents via async ROS2 service calls. No rclpy import."""

from control.commands.intent_parser import Intent
from control.commands.intent_parser import make_announcement_msg

PERCEPTION_INTENTS = {"describe_scene", "count_objects", "list_objects"}


class PerceptionBehavior:
    """Executes perception intents via ROS2 service calls on the owning node."""

    def __init__(self, node):
        self.node = node

    def handles(self, intent_name: str) -> bool:
        return intent_name in PERCEPTION_INTENTS

    def execute(self, intent: Intent, node=None) -> None:
        if intent.name == "describe_scene":
            self.call_describe_scene()
        elif intent.name == "list_objects":
            self.report_detections()
        elif intent.name == "count_objects":
            self.node.get_logger().warn("count_objects intent not yet implemented")

    def call_describe_scene(self) -> None:
        if not self.node.describe_scene_client.service_is_ready():
            self.node.get_logger().warn("/describe_scene service is not available")
            return
        from std_srvs.srv import Trigger  # lazy — avoids rclpy at import time
        future = self.node.describe_scene_client.call_async(Trigger.Request())
        future.add_done_callback(self.on_describe_scene_done)

    def on_describe_scene_done(self, future) -> None:
        try:
            response = future.result()
        except Exception as exc:
            self.node.get_logger().error(f"/describe_scene call failed: {exc}")
            return

        if not response.success:
            self.node.get_logger().warn(
                f"/describe_scene returned failure: {response.message}"
            )
            return

        self.publish_announcement(response.message)

    def report_detections(self) -> None:
        detections = getattr(self.node, "latest_detections", None)
        if detections is None or not detections.detections:
            self.publish_announcement("No objects detected.")
            return
        parts = []
        for det in detections.detections:
            if det.results:
                best = max(det.results, key=lambda r: r.hypothesis.score)
                label = best.hypothesis.class_id
                score = round(best.hypothesis.score, 2)
                parts.append(f"{label} {score}")
        text = "I see: " + ", ".join(parts) if parts else "No objects detected."
        self.publish_announcement(text)

    def publish_announcement(self, text: str) -> None:
        msg = make_announcement_msg(text)
        self.node.announcement_pub.publish(msg)
        self.node.get_logger().info(text)
