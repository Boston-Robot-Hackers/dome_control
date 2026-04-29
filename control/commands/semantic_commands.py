#!/usr/bin/env python3
# semantic_commands.py — user-facing semantic command aliases
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import control.commands.command_def as cd
import control.commands.parameter_def as pd


def build_semantic_commands() -> dict[str, cd.CommandDef]:
    return {
        "scene.describe": cd.CommandDef(
            method_name="publish_intent_describe_scene",
            parameters=[],
            description="Ask the behavior manager to describe the current scene",
            group="scene",
        ),
        "scene.count": cd.CommandDef(
            method_name="publish_intent_count_objects",
            parameters=[
                pd.ParameterDef(
                    "object_type", str, True, None, "Type of object to count"
                )
            ],
            description="Ask the behavior manager to count visible objects by type",
            group="scene",
        ),
    }
