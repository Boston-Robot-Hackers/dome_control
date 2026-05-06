#!/usr/bin/env python3
# remote.launch.py — ROS2 nodes that run on the remote/dev machine
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='control',
            executable='describe_scene_stub',
            name='describe_scene_stub',
            output='screen',
        ),
    ])
