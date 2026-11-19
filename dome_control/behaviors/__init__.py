#!/usr/bin/env python3
# __init__.py — behaviors package
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-11-19
# Updated: 2026-11-19
# Open Source Under MIT license
from dome_control.behaviors.motion_behavior import MotionBehavior
from dome_control.behaviors.perception_behavior import PerceptionBehavior

__all__ = ["MotionBehavior", "PerceptionBehavior"]
