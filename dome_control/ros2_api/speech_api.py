#!/usr/bin/env python3
# speech_api.py — publishes AnnouncementMsg to /announcement topic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import dome_control.commands.config_manager as cm
import dome_control.ros2_api.base_api as base
from dome_control.announcement_contract import Announcement, PRIORITY_CHITCHAT


class SpeechApi(base.BaseApi):

    def __init__(self, config_manager: cm.ConfigManager = None):
        super().__init__("speech_api", config_manager)
        from dome_control.announcement_contract import AnnouncementMsg
        self.announcement_pub = self.create_publisher(AnnouncementMsg, "/announcement", 10)

    def speak(self, text: str, priority: int = PRIORITY_CHITCHAT) -> None:
        ann = Announcement(text=text, priority=priority, source="cli")
        self.announcement_pub.publish(ann.to_msg())
        self.log_info(f"Speak published: {text!r}")
