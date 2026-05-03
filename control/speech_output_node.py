#!/usr/bin/env python3
"""ROS2 node: subscribe to /announcement and speak via Piper + ALSA."""

import os
import subprocess
import tempfile

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from control.announcement_contract import Announcement


def synthesize_to_wav(
    text: str,
    wav_path: str,
    piper_bin: str,
    model_path: str,
) -> None:
    """Synthesize text to wav_path using Piper."""
    if not model_path:
        raise RuntimeError("PIPER_MODEL_PATH is required for speech output")

    cmd = [piper_bin, "--model", model_path, "--output_file", wav_path]
    subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        check=True,
        capture_output=True,
    )


def play_wav(wav_path: str, alsa_device: str = "") -> None:
    """Play wav_path using ALSA aplay."""
    cmd = ["aplay"]
    if alsa_device:
        cmd.extend(["-D", alsa_device])
    cmd.append(wav_path)
    subprocess.run(cmd, check=True, capture_output=True)


class SpeechOutputNode(Node):
    def __init__(self):
        super().__init__("speech_output")
        self.announcement_sub = self.create_subscription(
            String, "/announcement", self.on_announcement, 10
        )
        self.piper_bin = os.environ.get("PIPER_BIN", "piper")
        self.piper_model_path = os.environ.get("PIPER_MODEL_PATH", "")
        self.alsa_device = os.environ.get("SPEECH_ALSA_DEVICE", "")
        self.tmp_dir = os.environ.get("SPEECH_TMP_DIR", tempfile.gettempdir())

    def on_announcement(self, msg: String) -> None:
        announcement = Announcement.from_payload(msg.data)
        if not announcement.text:
            self.get_logger().debug("Ignoring empty announcement payload")
            return

        try:
            self.speak_text(announcement.text)
            self.get_logger().info(
                f"Spoken announcement ({announcement.priority}) from "
                f"{announcement.source}: {announcement.text}"
            )
        except Exception as exc:
            self.get_logger().error(f"Speech output failed: {exc}")

    def _make_wav_path(self) -> str:
        fd, path = tempfile.mkstemp(prefix="speech-output-", suffix=".wav", dir=self.tmp_dir)
        os.close(fd)
        return path

    def speak_text(self, text: str) -> None:
        wav_path = self._make_wav_path()
        try:
            synthesize_to_wav(
                text=text,
                wav_path=wav_path,
                piper_bin=self.piper_bin,
                model_path=self.piper_model_path,
            )
            play_wav(wav_path, alsa_device=self.alsa_device)
        finally:
            try:
                os.remove(wav_path)
            except FileNotFoundError:
                pass


def main():
    rclpy.init()
    node = SpeechOutputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
