#!/usr/bin/env python3
# survey_api — ROS2 client for /survey/start service
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class SurveyApi(Node):
    def __init__(self):
        super().__init__("survey_api_client")
        self._client = self.create_client(Trigger, "/survey/start")

    def start(self, timeout_s: float = 5.0) -> tuple[bool, str]:
        if not self._client.wait_for_service(timeout_sec=timeout_s):
            return False, "/survey/start service not available — is spin_survey_node running?"
        future = self._client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_s)
        if not future.done():
            return False, "Service call timed out"
        result = future.result()
        return result.success, result.message
