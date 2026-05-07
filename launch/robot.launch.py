#!/usr/bin/env python3
# robot.launch.py — ROS2 nodes that run on the physical robot
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from better_launch import BetterLaunch, launch_this

PIPER_BIN = "/home/pitosalas/ros2_ws/src/control/bin/piper/piper"
PIPER_MODEL_PATH = (
    "/home/pitosalas/ros2_ws/src/control/piper_model/en_US-lessac-medium.onnx"
)


@launch_this(ui=False)
def robot_launch(voice: bool = False, behavior: bool = True):
    bl = BetterLaunch()

    bl.node(
        "control",
        "speech_output",
        "speech_output",
        env={
            "PIPER_BIN": PIPER_BIN,
            "PIPER_MODEL_PATH": PIPER_MODEL_PATH,
            "PIPER_LENGTH_SCALE": "1.0",
            "SPEECH_GAIN": "0.25",
            "SPEECH_ALSA_DEVICE": "plughw:0,0",
        },
    )

    bl.node(
        "control",
        "describe_scene_stub",
        "describe_scene_stub",
    )

    if behavior:
        bl.node(
            "control",
            "behavior_manager",
            "behavior_manager",
        )

    if voice:
        bl.node(
            "control",
            "voice_input",
            "voice_input",
        )
