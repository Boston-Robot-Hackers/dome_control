#!/usr/bin/env python3
# robot.launch.py — dome_control's nodes on the physical robot
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-11-17
# Updated: 2026-11-17
# Open Source Under MIT license
#
# Usage:
#   bl dome_control robot.launch.py              # this package alone
#   bl dome2 robot.launch.py --options "d c"     # via dome2's "control" subsystem
"""Start dome_control's robot-side nodes.

Starts behavior_manager, telemetry and spin_survey. spin_survey's params come
from config/spin_survey.yaml. Per stack/launch_conventions.md this file starts
only dome_control's own nodes; dome2 combines it with other packages.
"""

from better_launch import BetterLaunch, launch_this


@launch_this(ui=True)
def robot_launch():
    """Start behavior_manager, telemetry and spin_survey. Takes no arguments."""
    bl = BetterLaunch()

    bl.node("dome_control", "behavior_manager", "behavior_manager")
    bl.node("dome_control", "telemetry_node", "telemetry")
    bl.node(
        "dome_control",
        "spin_survey_node",
        "spin_survey",
        param_files=bl.find("dome_control", "spin_survey.yaml"),
        ros_waittime=10.0,
    )
