#!/usr/bin/env python3
# test_behavior_manager_class_profiles.py — default class profiles come from dome_semantic
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
# Test tier: needs the sourced workspace (dome_semantic installed), no ROS runtime
from dome_semantic.class_profiles import build_label_map, load_class_profiles

from dome_control.nodes.behavior_manager_node import default_class_profiles_path


def test_default_path_loads_dome_semantic_profiles():
    profiles = load_class_profiles(default_class_profiles_path())
    assert {"can", "cup"} <= set(profiles)


def test_default_profiles_map_can_to_its_class():
    label_map = build_label_map(load_class_profiles(default_class_profiles_path()))
    assert label_map["can"] == "can"
