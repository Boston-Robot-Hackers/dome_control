#!/usr/bin/env python3
# survey_commands — survey command definitions
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import dome_control.commands.command_def as cd


def build_survey_commands() -> dict[str, cd.CommandDef]:
    return {
        "survey.start": cd.CommandDef(
            method_name="start_survey",
            parameters=[],
            description="Start a 360° spin survey to build the semantic map",
            group="survey",
        ),
    }
