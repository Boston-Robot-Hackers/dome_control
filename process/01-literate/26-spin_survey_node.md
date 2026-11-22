---
version: "1.0"
generated: "2026-05-14"
---

# SpinSurveyNode: Survey Trigger and Tick Driver

`SpinSurveyNode` is a regular ROS2 `Node` (not a lifecycle node) that wraps `SpinSurvey`. It is always included in the full-stack launch and stays idle until the `/survey/start` service is called.

## Design Decision: Service-Triggered

The node does nothing at startup. It waits for a `Trigger` service call on `/survey/start`. This matches the real use case: the robot launches, localizes, then a CLI or behavior triggers the survey explicitly. A lifecycle-managed auto-start would require external activation logic for no benefit.

## Published Topics

| Topic | Type | When |
|-------|------|------|
| `/cmd_vel` | `geometry_msgs/Twist` | Every tick while running (angular.z only) |
| `/spin_survey/paused` | `std_msgs/Bool` | Every tick (True during pause phases) |
| `/spin_survey/done` | `std_msgs/Bool` | Once, on survey completion |

## Tick Rate

`TICK_HZ = 5` — 200ms per tick. At `angular_velocity=0.3 rad/s` and `step_angle_rad=0.872 rad` (50°), each step takes ~2.9s = ~14 ticks. The tick rate is low enough to not stress the executor and high enough for smooth pause detection.

## Parameter Defaults

All parameters come from `SpinSurveyConfig`:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `angular_velocity` | 0.3 | rad/s spin speed |
| `total_angle` | 6.2832 (2π) | full 360° pass |
| `step_angle_rad` | 1.047 | 60° per step |
| `pause_s` | 1.0 | seconds per pause |
| `pass_count` | 1 | number of passes |
| `pass_offset_rad` | 0.0 | inter-pass offset (0 → step/2) |

## Survey Flow

```
/survey/start called
    │
    ├── already running?  → return success=False, "already in progress"
    └── idle?
            │
            ▼
        build SpinSurvey from params
        survey.start()
        create_timer(1/TICK_HZ, self.tick)
            │
            ▼ tick() × N
            │
            └── done → destroy_timer, publish done=True, survey=None
```

## Integration with dome_vision

`SemanticMapNode` subscribes to `/spin_survey/done` and uses it as the trigger to persist the semantic map. `dome_vision/launch/full_stack.launch.py` and `robot.launch.py` both include `SpinSurveyNode` from the `dome_control` package.
