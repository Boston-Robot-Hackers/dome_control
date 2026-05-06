#!/usr/bin/env python3
# robot.launch.py — ROS2 nodes that run on the physical robot
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='control',
            executable='behavior_manager',
            name='behavior_manager',
            output='screen',
        ),
        Node(
            package='control',
            executable='speech_output',
            name='speech_output',
            output='screen',
            additional_env={
                'PIPER_BIN': '/home/pitosalas/ros2_ws/src/control/bin/piper/piper',
                'PIPER_MODEL_PATH': '/home/pitosalas/ros2_ws/src/control/piper_model/en_US-lessac-medium.onnx',
                'PIPER_LENGTH_SCALE': '1.0',
                'SPEECH_GAIN': '0.25',
            },
        ),
        Node(
            package='control',
            executable='voice_input',
            name='voice_input',
            output='screen',
        ),
    ])
