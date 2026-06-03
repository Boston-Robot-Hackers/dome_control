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

    bl.node(
        "dome_control",
        "telemetry_node",
        "telemetry",
    )

    bl.node(
        "dome_control",
        "spin_survey_node",
        "spin_survey",
        params={
            "angular_velocity": 0.3,
            "total_angle": 6.2832,
            "step_angle_rad": 0.5,
            "pause_s": 1.0,
            "pass_count": 2,
            "pass_offset_rad": 0.5,
        },
        ros_waittime=10.0,
    )
