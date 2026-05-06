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
        ),
        Node(
            package='control',
            executable='voice_input',
            name='voice_input',
            output='screen',
        ),
    ])
