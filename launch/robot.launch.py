#!/usr/bin/env python3
# robot.launch.py — control nodes for the physical robot
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from better_launch import BetterLaunch, launch_this

@launch_this(ui=True)
def robot_launch():
    bl = BetterLaunch()

    bl.node(
        "dome_control",
        "behavior_manager",
        "behavior_manager",
    )
