#!/usr/bin/env python3
# test_spin_survey_params — config/spin_survey.yaml matches SpinSurveyConfig
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-11-17
# Updated: 2026-11-17
# Open Source Under MIT license
"""Check that spin_survey.yaml sets exactly SpinSurveyConfig's fields.

The node declares one parameter per SpinSurveyConfig field, so a key in the
YAML that is not a field would be silently ignored at launch.
"""

from pathlib import Path

import yaml

from dome_control.spin_survey import SpinSurveyConfig

PARAMS_PATH = Path(__file__).parent.parent / "config" / "spin_survey.yaml"


def load_tuning() -> dict:
    return yaml.safe_load(PARAMS_PATH.read_text())["spin_survey"]["ros__parameters"]


def test_yaml_keys_are_config_fields():
    assert set(load_tuning()) == set(SpinSurveyConfig.model_fields)


def test_yaml_values_validate_against_config():
    SpinSurveyConfig(**load_tuning())
