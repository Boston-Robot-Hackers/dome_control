#!/usr/bin/env python3
# intent_api.py — publishes normalized intent messages to /intent topic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
import time

from std_msgs.msg import String

import control.commands.config_manager as cm
import control.ros2_api.base_api as base

REPLY_INTENTS = {"describe_scene", "list_objects", "get_status", "get_help"}
REPLY_TIMEOUT_S = 5.0


class IntentApi(base.BaseApi):

    def __init__(self, config_manager: cm.ConfigManager = None):
        super().__init__("intent_api", config_manager)
        self.intent_pub = self.create_publisher(String, "/intent", 10)
        self._reply_text: str | None = None
        from control.announcement_contract import AnnouncementMsg
        self.create_subscription(AnnouncementMsg, "/announcement", self._on_announcement, 10)

    def _on_announcement(self, msg) -> None:
        self._reply_text = msg.text

    def publish(self, name: str, source: str, slots: dict) -> str | None:
        msg = String()
        msg.data = json.dumps({"name": name, "source": source, "slots": slots})
        self.intent_pub.publish(msg)
        self.log_info(f"Intent published: {msg.data}")

        if name not in REPLY_INTENTS:
            return None

        self._reply_text = None
        deadline = time.monotonic() + REPLY_TIMEOUT_S
        import rclpy
        while time.monotonic() < deadline and self._reply_text is None:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self._reply_text
