#!/usr/bin/env python3
# intent_publisher.py — thin helper to publish intents to /intent topic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Publishes intent JSON to /intent. Accepts injected publish_fn for testing."""

import json
from typing import Callable


class IntentPublisher:
    """Publishes intent JSON to /intent topic.

    Pass publish_fn for testing to avoid ROS2 dependency.
    In production, leave publish_fn=None — IntentApi is created lazily.
    """

    def __init__(self, publish_fn: Callable[[str], None] | None = None):
        self.publish_fn = publish_fn
        self.api = None

    def publish(
        self, name: str, source: str = "cli", slots: dict | None = None
    ) -> None:
        payload = json.dumps({"name": name, "source": source, "slots": slots or {}})
        if self.publish_fn is not None:
            self.publish_fn(payload)
        else:
            self.get_api().publish(name, source, slots or {})

    def get_api(self):
        if self.api is None:
            from control.ros2_api.intent_api import IntentApi
            from control.commands.config_manager import ConfigManager
            self.api = IntentApi(ConfigManager())
        return self.api
