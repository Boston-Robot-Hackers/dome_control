#!/usr/bin/env python3
"""ROS2 node: openWakeWord + Vosk STT + intent mapper → /intent."""

import json
import os
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from control.voice.wake_word import WakeWordDetector
from control.voice.stt import SpeechTranscriber
from control.voice.intent_mapper import map_intent
from control.voice.audio_feedback import beep, speak

VOICE_STATES = ("IDLE", "LISTENING", "PROCESSING")


class VoiceInputNode(Node):
    def __init__(self):
        super().__init__("voice_input")
        self.intent_pub = self.create_publisher(String, "/intent", 10)
        self.state_pub = self.create_publisher(String, "/voice/state", 10)
        self.announcement_pub = self.create_publisher(String, "/announcement", 10)

    def publish_intent(self, intent: dict) -> None:
        msg = String()
        msg.data = json.dumps(intent)
        self.intent_pub.publish(msg)
        self.get_logger().info(f"Intent published: {msg.data}")

    def publish_state(self, state: str) -> None:
        msg = String()
        msg.data = state
        self.state_pub.publish(msg)
        self.get_logger().info(f"Voice state: {state}")

    def publish_announcement(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.announcement_pub.publish(msg)


def main():
    device_index = int(os.environ.get("VOICE_DEVICE_INDEX", "0"))

    rclpy.init()
    node = VoiceInputNode()
    detector = WakeWordDetector(device_index=device_index)
    transcriber = SpeechTranscriber(device_index=device_index)

    try:
        node.get_logger().info("Voice input ready — listening for 'Hey Jarvis'")
        node.publish_state("IDLE")

        while rclpy.ok():
            detector.start()
            detected = detector.wait_for_wake(ok_fn=rclpy.ok)
            detector.stop()

            if not detected:
                break

            node.get_logger().info("Wake word detected — speak your command")
            node.publish_state("LISTENING")
            beep(frequency=880, duration=0.02, device_index=device_index)

            text = transcriber.transcribe()
            node.get_logger().info(f"Transcribed: '{text}'")
            node.publish_state("PROCESSING")

            intent = map_intent(text)
            if intent:
                node.publish_intent(intent)
            else:
                speak("say again")
                node.publish_announcement("I didn't catch that")

            node.publish_state("IDLE")
            beep(frequency=330, duration=0.02, device_index=device_index)

    finally:
        detector.close()
        transcriber.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
