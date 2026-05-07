#!/usr/bin/env python3
# remote.launch.py — ROS2 nodes that run on the remote/dev machine
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from better_launch import BetterLaunch, launch_this


@launch_this(ui=False)
def remote_launch(voice: bool = True, behavior: bool = False):
    bl = BetterLaunch()

    if voice:
        bl.node(
            "control",
            "voice_input",
            "voice_input",
        )

    if behavior:
        bl.node(
            "control",
            "behavior_manager",
            "behavior_manager",
        )
