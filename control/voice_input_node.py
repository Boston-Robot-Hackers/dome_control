#!/usr/bin/env python3
# voice_input_node.py - temporary Porcupine-to-/intent bridge
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""ROS2 node that publishes a describe_scene intent when Porcupine hears Jarvis."""

import json
import os
from typing import Callable

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


INTENT_PAYLOAD = {"name": "describe_scene", "source": "voice", "slots": {}}


class VoiceInputNode(Node):
    def __init__(self):
        super().__init__("voice_input")
        self.intent_pub = self.create_publisher(String, "/intent", 10)

    def publish_describe_scene_intent(self) -> None:
        msg = String()
        msg.data = json.dumps(INTENT_PAYLOAD)
        self.intent_pub.publish(msg)
        self.get_logger().info(f"Voice intent published: {msg.data}")


def _load_picovoice():
    try:
        import pvporcupine
        from pvrecorder import PvRecorder
    except ImportError as exc:
        raise RuntimeError(
            "Install voice dependencies first: "
            "pip install pvporcupine pvrecorder pvporcupinedemo"
        ) from exc
    return pvporcupine, PvRecorder


def run_porcupine_loop(
    on_wake: Callable[[], None],
    access_key: str,
    keyword: str = "jarvis",
    device_index: int = -1,
) -> None:
    pvporcupine, PvRecorder = _load_picovoice()
    porcupine = pvporcupine.create(access_key=access_key, keywords=[keyword])
    recorder = PvRecorder(
        device_index=device_index,
        frame_length=porcupine.frame_length,
    )

    try:
        recorder.start()
        while rclpy.ok():
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                on_wake()
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()


def main():
    access_key = os.environ.get("PICOVOICE_ACCESS_KEY")
    if not access_key:
        raise RuntimeError("Set PICOVOICE_ACCESS_KEY before running voice_input")

    device_index = int(os.environ.get("PICOVOICE_DEVICE_INDEX", "-1"))

    rclpy.init()
    node = VoiceInputNode()
    try:
        node.get_logger().info("Listening for Porcupine wake word: jarvis")
        run_porcupine_loop(
            on_wake=node.publish_describe_scene_intent,
            access_key=access_key,
            device_index=device_index,
        )
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
