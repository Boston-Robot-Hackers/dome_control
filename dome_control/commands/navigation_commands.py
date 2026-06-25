#!/usr/bin/env python3
"""
Navigation Commands - Map management command definitions
Author: Pito Salas and Claude Code
Open Source Under MIT license
"""
import dome_control.commands.command_def as cd
import dome_control.commands.parameter_def as pd


def build_navigation_commands() -> dict[str, cd.CommandDef]:
    return {
        "map.save": cd.CommandDef(
            method_name="map_save",
            parameters=[],
            description="Save current map to maps/ folder (uses map_name variable)",
            group="map"
        ),
        "map.list": cd.CommandDef(
            method_name="list_maps",
            parameters=[],
            description="List available maps in maps/ folder",
            group="map"
        ),
        "map.serialize": cd.CommandDef(
            method_name="map_serialize",
            parameters=[],
            description="Save current map in SLAM Toolbox serialized format (uses map_name variable)",
            group="map"
        ),
        "nav.go": cd.CommandDef(
            method_name="publish_intent_navigation_go",
            parameters=[pd.ParameterDef("label", str, True, None, "Object label to navigate to")],
            description="Navigate to nearest confirmed object with given label",
            group="nav"
        ),
        "nav.cancel": cd.CommandDef(
            method_name="publish_intent_navigation_cancel",
            parameters=[],
            description="Cancel current navigation goal",
            group="nav"
        ),
        "nav.explore": cd.CommandDef(
            method_name="publish_intent_exploration_start",
            parameters=[],
            description="Start autonomous frontier exploration",
            group="nav"
        ),
        "nav.explore.stop": cd.CommandDef(
            method_name="publish_intent_exploration_stop",
            parameters=[],
            description="Stop autonomous frontier exploration",
            group="nav"
        ),
        "nav.explore.status": cd.CommandDef(
            method_name="explore_status",
            parameters=[],
            description="Read current /explore/status topic value",
            group="nav"
        ),
    }
