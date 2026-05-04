---
version: "1.0"
generated: "2026-05-04"
---

# CalibrationApi

`calibration_api.py` provides scripted movement patterns for calibration and stress testing. It sits above `MovementApi` in the dependency chain and delegates all actual motion to it.

## Structure

```python
class CalibrationApi(base.BaseApi):
    def __init__(self, movement_api: movement.MovementApi, config_manager: cm.ConfigManager):
        super().__init__("calibration_api", config_manager)
        self.movement = movement_api
```

`CalibrationApi` receives an existing `MovementApi` instance rather than constructing its own. This matters because `MovementApi` is a ROS2 node (it registers publishers and subscribers). Creating a second `MovementApi` would create a second `movement_api` node with duplicate pub/sub connections.

## Square Pattern

```python
def run_square_pattern(self, side_length: float):
    for i in range(4):
        self.movement.move_dist(side_length)
        self.movement.turn_amount(math.pi / 2)
```

Drives four equal sides with 90-degree turns between them. Because `move_dist` and `turn_amount` are open-loop (time-based), accumulated heading error means the robot does not return to exactly the starting point. The square pattern is useful for measuring that accumulated error.

## Rotation Stress Test

```python
def run_rotate_stress(self):
    slow_angular = self.config.get_variable("stress_test_rotation_speed") or 0.2
    full_rotation = 2 * math.pi
    ...
    while rclpy.ok():
        for rotation in range(10):
            time_for_rotation = full_rotation / slow_angular
            self.movement.cmd_vel_helper(0.0, slow_angular, time_for_rotation)
```

Runs in an infinite loop until `KeyboardInterrupt`. Each cycle completes 10 full rotations. The rotation speed comes from config (`stress_test_rotation_speed`), allowing tuning without code changes. `_print_elapsed_time` logs progress every 10 seconds so the operator knows the test is still running.

## Circle Stress Test

```python
def run_circle_stress(self, diameter: float):
    radius = diameter / 2.0
    circumference = 2 * math.pi * radius
    circle_time = circumference / linear_speed
    self.movement.cmd_vel_helper(linear_speed, angular_speed, circle_time)
```

For a circle of a given diameter, the required angular velocity is `v / r` (linear speed divided by radius). This value must be set in config as `angular_speed` before running — there's no automatic calculation of the correct angular speed from the diameter. If the configured `angular_speed` doesn't match `linear_speed / radius`, the robot traces an arc rather than a circle.

## Observations

- The circle stress test silently produces wrong geometry if `angular_speed` isn't set to `linear_speed / radius`. A `log_warn` when the computed ratio differs significantly from the configured value would help.
- Both stress tests catch `KeyboardInterrupt` and call `self.movement.stop()`. This is good practice — without it, a Ctrl+C mid-motion would leave the robot moving.
- `_print_elapsed_time` is a helper that returns `current_time` if it logged, `last_print_time` if not. The pattern is slightly awkward; a simple counter or `time.time()` modulo check would be cleaner.
