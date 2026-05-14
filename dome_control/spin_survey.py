#!/usr/bin/env python3
# spin_survey — SpinSurvey: 360° in-place spin behavior, no ROS2 imports
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import math

from pydantic import BaseModel


class SpinSurveyConfig(BaseModel):
    angular_velocity: float = 0.3
    total_angle: float = math.tau
    step_angle_rad: float = 1.047
    pause_s: float = 1.0
    pass_count: int = 1
    pass_offset_rad: float = 0.0


class SpinSurvey:
    """Drive robot in a 360° in-place spin while inference runs alongside.

    Two modes:
    - Continuous (step_angle_rad=0): publishes angular_velocity every tick until done.
    - Step-spin (step_angle_rad>0): alternates spin phase (rotate step_angle_rad) and
      pause phase (hold 0.0 for pause_s). Gives camera time to capture sharp frames.

    Caller pumps tick() at a fixed rate; SpinSurvey returns the angular
    velocity to publish each tick and signals when the spin is complete.
    No ROS2, no hardware imports.
    """

    def __init__(
        self,
        angular_velocity_rad_s: float,
        total_angle_rad: float = 2 * math.pi,
        step_angle_rad: float = 0.0,
        pause_s: float = 1.0,
        pass_count: int = 1,
        pass_offset_rad: float | None = None,
    ):
        self.angular_velocity_rad_s = angular_velocity_rad_s
        self.total_angle_rad = total_angle_rad
        self.step_angle_rad = step_angle_rad
        self.pause_s = pause_s
        self.pass_count = pass_count
        self.pass_offset_rad = pass_offset_rad
        self.elapsed_s: float = 0.0
        self.started: bool = False
        self.angle_rotated: float = 0.0
        self.pause_elapsed_s: float = 0.0
        self.is_pausing: bool = False
        self.pass_num: int = 1
        self.is_inter_pass: bool = False
        self.inter_pass_elapsed_s: float = 0.0

    def start(self) -> float:
        """Mark spin started; return angular velocity to publish on first tick."""
        self.started = True
        self.elapsed_s = 0.0
        self.angle_rotated = 0.0
        self.pause_elapsed_s = 0.0
        self.is_pausing = False
        self.pass_num = 1
        self.is_inter_pass = False
        self.inter_pass_elapsed_s = 0.0
        return self.angular_velocity_rad_s

    def tick(self, elapsed_s: float) -> tuple[float, bool]:
        """Advance elapsed time; return (cmd_vel_z, done)."""
        if self.is_done():
            return (0.0, True)
        if self.is_inter_pass:
            return self.inter_pass_tick(elapsed_s)
        if self.step_angle_rad <= 0.0:
            self.elapsed_s += elapsed_s
            return (0.0, True) if self.is_done() else (self.angular_velocity_rad_s, False)
        return self.step_tick(elapsed_s)

    def inter_pass_tick(self, elapsed_s: float) -> tuple[float, bool]:
        offset = self.pass_offset_rad if self.pass_offset_rad is not None else self.step_angle_rad / 2.0
        offset_duration = offset / self.angular_velocity_rad_s
        self.inter_pass_elapsed_s += elapsed_s
        if self.inter_pass_elapsed_s >= offset_duration:
            self.is_inter_pass = False
            self.elapsed_s = 0.0
            self.angle_rotated = 0.0
            self.pause_elapsed_s = 0.0
            self.is_pausing = False
        return (self.angular_velocity_rad_s, False)

    def step_tick(self, elapsed_s: float) -> tuple[float, bool]:
        if self.is_pausing:
            self.pause_elapsed_s += elapsed_s
            if self.pause_elapsed_s >= self.pause_s:
                self.is_pausing = False
                self.pause_elapsed_s = 0.0
                if self.pass_done() and self.pass_num < self.pass_count:
                    self.pass_num += 1
                    self.is_inter_pass = True
                    self.inter_pass_elapsed_s = 0.0
            return (0.0, False)
        angle_this_tick = self.angular_velocity_rad_s * elapsed_s
        self.angle_rotated += angle_this_tick
        self.elapsed_s += elapsed_s
        if self.angle_rotated >= self.step_angle_rad:
            self.angle_rotated = 0.0
            self.is_pausing = True
        if self.is_done():
            return (0.0, True)
        return (self.angular_velocity_rad_s, False)

    def pass_done(self) -> bool:
        """True when accumulated elapsed time covers one full pass rotation."""
        duration = self.total_angle_rad / self.angular_velocity_rad_s
        return self.elapsed_s >= duration

    @property
    def is_paused(self) -> bool:
        return self.is_pausing and not self.is_inter_pass

    def is_done(self) -> bool:
        """True when all passes complete."""
        if self.is_inter_pass:
            return False
        if self.pass_num < self.pass_count:
            return False
        duration = self.total_angle_rad / self.angular_velocity_rad_s
        return self.elapsed_s >= duration
