#!/usr/bin/env python3
"""ROS2 node: openWakeWord + Vosk STT + intent mapper → /intent."""

import json
import os

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from control.announcement_contract import (
    AnnouncementMsg,
    PRIORITY_QUERY_REPLY,
    make_announcement_msg,
)
from control.voice.audio_feedback import beep, speak
from control.voice.intent_mapper import IntentMapper
from control.voice.stt import SpeechTranscriber
from control.voice.wake_word import WakeWordDetector

VOICE_STATES = ("IDLE", "LISTENING", "PROCESSING", "SPEAKING")


class VoiceInputNode(Node):
    def __init__(self):
        super().__init__("voice_input")
        self.intent_pub = self.create_publisher(String, "/intent", 10)
        self.state_pub = self.create_publisher(String, "/voice/state", 10)
        self.announcement_pub = self.create_publisher(
            AnnouncementMsg, "/announcement", 10
        )
        self.intent_mapper = IntentMapper()

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
        msg = make_announcement_msg(
            text,
            priority=PRIORITY_QUERY_REPLY,
            source="voice_input",
        )
        self.announcement_pub.publish(msg)

    def process_transcript(self, text: str, device_index: int = 0) -> None:
        self.get_logger().info(f"Transcribed: '{text}'")
        self.publish_state("PROCESSING")

        intent = self.intent_mapper.map_intent(text)
        if intent:
            self.publish_intent(intent)
            self.publish_state("SPEAKING")
            beep(frequency=330, duration=0.02, device_index=device_index)
        else:
            self.publish_state("SPEAKING")
            speak("say again")
            self.publish_announcement("I didn't catch that")


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
            node.process_transcript(text, device_index=device_index)
            node.publish_state("IDLE")

    finally:
        detector.close()
        transcriber.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
