#!/usr/bin/env python3
# test_spin_survey — unit tests for SpinSurvey
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import math
import pytest
from dome_control.spin_survey import SpinSurvey


def test_start_returns_angular_velocity():
    s = SpinSurvey(angular_velocity_rad_s=0.3)
    vel = s.start()
    assert vel == pytest.approx(0.3)


def test_not_done_before_full_rotation():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=2 * math.pi)
    s.start()
    # Duration = 2π / 0.3 ≈ 20.94 s; tick with half that time
    _, done = s.tick(10.0)
    assert done is False


def test_done_after_full_rotation_elapsed():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=2 * math.pi)
    s.start()
    duration = 2 * math.pi / 0.3
    _, done = s.tick(duration)
    assert done is True


def test_cmd_vel_z_correct_during_spin():
    s = SpinSurvey(angular_velocity_rad_s=0.5, total_angle_rad=2 * math.pi)
    s.start()
    vel, done = s.tick(1.0)
    assert done is False
    assert vel == pytest.approx(0.5)


def test_cmd_vel_z_zero_when_done():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=math.pi)
    s.start()
    duration = math.pi / 0.3
    vel, done = s.tick(duration + 1.0)
    assert done is True
    assert vel == pytest.approx(0.0)


def test_is_done_false_before_completion():
    s = SpinSurvey(angular_velocity_rad_s=0.3)
    s.start()
    s.tick(5.0)
    assert s.is_done() is False


def test_is_done_true_after_completion():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=math.pi)
    s.start()
    duration = math.pi / 0.3
    s.tick(duration)
    assert s.is_done() is True


def test_cumulative_ticks_trigger_completion():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi)
    s.start()
    duration = math.pi  # pi radians / 1.0 rad/s
    # Feed many small ticks summing to > duration
    steps = 20
    dt = duration / steps
    done = False
    for _ in range(steps + 1):
        _, done = s.tick(dt)
    assert done is True


def test_custom_total_angle():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi / 2)
    s.start()
    # half-rotation completes in π/2 seconds
    _, done = s.tick(math.pi / 2)
    assert done is True


# --- step-spin mode tests ---

def test_step_spin_spins_during_spin_phase():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.174, pause_s=1.0)
    s.start()
    vel, done = s.tick(0.1)
    assert done is False
    assert vel == pytest.approx(0.3)


def test_step_spin_pauses_after_step():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.1, pause_s=1.0)
    s.start()
    # tick long enough to complete the step
    s.tick(0.15)
    # now in pause phase — next tick should return 0.0
    vel, done = s.tick(0.1)
    assert vel == pytest.approx(0.0)
    assert done is False


def test_step_spin_resumes_after_pause():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.1, pause_s=0.5)
    s.start()
    s.tick(0.15)   # complete step → enter pause
    s.tick(0.6)    # exhaust pause
    vel, _ = s.tick(0.05)
    assert vel == pytest.approx(1.0)


def test_step_spin_completes_after_full_rotation():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.1, pause_s=0.01)
    s.start()
    duration = math.pi  # elapsed spin time needed
    done = False
    for _ in range(500):
        _, done = s.tick(0.05)
        if done:
            break
    assert done is True


def test_step_spin_zero_step_is_continuous():
    s = SpinSurvey(angular_velocity_rad_s=0.3, total_angle_rad=math.pi, step_angle_rad=0.0)
    s.start()
    vel, done = s.tick(1.0)
    assert vel == pytest.approx(0.3)
    assert done is False


def test_is_paused_false_during_spin_phase():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.5, pause_s=1.0)
    s.start()
    s.tick(0.1)
    assert s.is_paused is False


def test_is_paused_true_during_pause_phase():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.1, pause_s=1.0)
    s.start()
    s.tick(0.15)  # complete step → enter pause
    assert s.is_paused is True


def test_is_paused_false_in_continuous_mode():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=2 * math.pi,
                   step_angle_rad=0.0)
    s.start()
    s.tick(0.1)
    assert s.is_paused is False


# --- two-pass mode tests ---

def test_two_pass_not_done_after_pass1():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.5, pause_s=0.01, pass_count=2)
    s.start()
    duration = math.pi
    for _ in range(500):
        _, done = s.tick(0.05)
        if s.pass_num == 2:
            break
    assert s.is_done() is False


def test_two_pass_inter_pass_is_not_paused():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.5, pause_s=0.01, pass_count=2,
                   pass_offset_rad=0.25)
    s.start()
    for _ in range(500):
        s.tick(0.05)
        if s.is_inter_pass:
            break
    assert s.is_inter_pass is True
    assert s.is_paused is False


def test_two_pass_inter_pass_velocity():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.5, pause_s=0.01, pass_count=2,
                   pass_offset_rad=0.25)
    s.start()
    for _ in range(500):
        s.tick(0.05)
        if s.is_inter_pass:
            vel, _ = s.tick(0.05)  # first tick actually in inter-pass
            assert vel == pytest.approx(1.0)
            break


def test_two_pass_done_after_pass2():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.5, pause_s=0.01, pass_count=2,
                   pass_offset_rad=0.25)
    s.start()
    done = False
    for _ in range(2000):
        _, done = s.tick(0.05)
        if done:
            break
    assert done is True


def test_pass_count_1_default_no_regression():
    s = SpinSurvey(angular_velocity_rad_s=1.0, total_angle_rad=math.pi,
                   step_angle_rad=0.1, pause_s=0.01)
    s.start()
    done = False
    for _ in range(500):
        _, done = s.tick(0.05)
        if done:
            break
    assert done is True
    assert s.pass_num == 1
