---
version: "1.0"
generated: "2026-05-14"
---

# SpinSurvey: 360° Spin State Machine

`SpinSurvey` drives a robot in a 360° in-place spin so a perception pipeline can build a full-room view. It has no ROS2 imports — it is pure Python business logic. The caller (a ROS2 node) pumps `tick()` at a fixed rate and publishes the returned velocity.

## Two Spin Modes

**Continuous** (`step_angle_rad=0`): publishes `angular_velocity` every tick until `elapsed_s` exceeds `total_angle_rad / angular_velocity`. Fastest full rotation; blurry frames are possible.

**Step-spin** (`step_angle_rad>0`): alternates between a spin phase and a pause phase.

```
spin phase: rotate step_angle_rad at angular_velocity
pause phase: hold 0.0 for pause_s seconds
repeat until total_angle_rad accumulated
```

Default `step_angle_rad=1.047` (60°) with `pause_s=1.0` gives the camera a clean stationary window each step.

## Multi-Pass

`pass_count>1` runs multiple full rotations. Between passes, an optional inter-pass offset rotation (`pass_offset_rad`) repositions the starting angle to reduce overlap with the previous pass. If `pass_offset_rad` is 0 the offset defaults to `step_angle_rad / 2`.

## State Variables

```python
self.elapsed_s          # time accumulated in current pass
self.angle_rotated      # angle in current step (resets after each step)
self.is_pausing         # True during pause phase
self.pause_elapsed_s    # time elapsed in current pause
self.pass_num           # which pass (1-based)
self.is_inter_pass      # True during inter-pass offset rotation
self.inter_pass_elapsed_s
```

## tick() Return Contract

```python
vel, done = survey.tick(elapsed_s)
# vel: angular_velocity_rad_s (spinning) or 0.0 (pausing / done)
# done: True when all passes complete
```

Caller should stop its timer when `done` is True. `SpinSurvey` itself does nothing with the timer.

## Lifecycle

```
SpinSurvey(...)
    │
    ▼ survey.start()          ← reset all state, return initial vel
    │
    ▼ survey.tick(dt) × N     ← pump at fixed rate
    │
    └── (vel=0, done=True)    ← all passes complete
```

`start()` is idempotent — calling it again resets the survey and returns the first velocity.

## Observations

- `pass_done()` checks accumulated `elapsed_s` against `total_angle_rad / angular_velocity_rad_s`. Because ticks are discrete, the survey may overshoot slightly before `is_done()` returns True. The effect is ≤ one tick period (200ms at TICK_HZ=5).
- Inter-pass offset duration is computed from `pass_offset_rad / angular_velocity_rad_s` — so a larger velocity makes the inter-pass shorter in time but the same in angle.
