#!/usr/bin/env python3
# __init__.py — behaviors package
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
from dome_control.behaviors.motion_behavior import MotionBehavior
from dome_control.behaviors.perception_behavior import PerceptionBehavior

__all__ = ['MotionBehavior', 'PerceptionBehavior']
