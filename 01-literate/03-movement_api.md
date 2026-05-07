---
version: "1.2"
generated: "2026-05-06"
---

# MovementApi: Velocity Control and Odometry

`MovementApi` is the thin ROS2 layer between the robot's wheels and the command layer. It publishes `Twist` messages to `/cmd_vel` and subscribes to `/odom`. All movement commands in the stack eventually call one of its three primitives: `cmd_vel_helper`, `turn_amount`, or `stop`.

## Inheriting from BaseApi

`MovementApi` extends `BaseApi`, which wraps `rclpy.Node`. This gives it access to `create_publisher`, `create_subscription`, `log_info`, and the `config` property without re-implementing node boilerplate.

```python
class MovementApi(base.BaseApi):
    def __init__(self, config_manager: cm.ConfigManager = None):
        super().__init__("movement_api", config_manager)
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 1)
        self.odom_sub = self.create_subscription(
            Odometry, "/odom", self.odom_callback, 10
        )
        self._validate_config()
        self.current_pose = None
```

A queue depth of 1 for `cmd_vel` is intentional: if the robot can't keep up with commands, the newest command should win, not queue behind stale ones.

## Speed as Config Properties

Rather than capturing speeds at construction time, each speed is a live property reading from `ConfigManager`. This means `config set linear_speed 0.4` takes effect on the next movement call without restarting the node:

```python
@property
def linear(self) -> float:
    return self.config.get_variable("linear_speed")
```

The same pattern applies to `angular`, `linear_min`, `linear_max`, `angular_min`, `angular_max`.

## Config Validation at Startup

The six speed variables are required. `_validate_config` checks all of them at construction time so failures are loud and early rather than silent `None` math errors mid-movement:

```python
def _validate_config(self):
    required_vars = ["linear_speed", "angular_speed",
                     "linear_min", "linear_max", "angular_min", "angular_max"]
    missing = [v for v in required_vars if self.config.get_variable(v) is None]
    if missing:
        raise ValueError(f"Missing required configuration variables: {', '.join(missing)}")
```

## The Central Primitive: cmd_vel_helper

All movement boils down to this method — publish a `Twist` at 10 Hz for a given duration, then stop:

```python
def cmd_vel_helper(self, linear: float, angular: float, seconds: float):
    if not self.blocking_ok:
        raise RuntimeError("cmd_vel_helper called from a non-blocking context")
    if not self.check_velocity_limits(linear, angular):
        return
    if self.config.is_dry_run():
        self.log_info(f"DRY RUN: Would move linear={linear}, angular={angular} for {seconds}s")
        return

    twist = Twist()
    twist.linear.x = linear
    twist.angular.z = angular
    start_time = time.time()
    rate_hz = 10
    sleep_duration = 1.0 / rate_hz
    while rclpy.ok() and (time.time() - start_time) < seconds:
        self.cmd_vel_pub.publish(twist)
        time.sleep(sleep_duration)

    twist.linear.x = 0.0
    twist.angular.z = 0.0
    self.cmd_vel_pub.publish(twist)
```

The 10 Hz re-publish loop is needed because many ROS2 motor drivers treat a stale `/cmd_vel` as a stop command. The explicit zero-velocity stop at the end is a safety measure.

### Why Not spin_once?

An earlier version called `rclpy.spin_once(self, timeout_sec=sleep_duration)` inside the loop. This crashed with `RuntimeError: Executor is already spinning` when `cmd_vel_helper` was invoked from within a `BehaviorManagerNode` callback (already being spun by `rclpy.spin`). Publishers do not need executor spinning — only subscribers do. Removing `spin_once` and replacing it with `time.sleep` fixes the nested-spin crash. The tradeoff is that the odometry subscription (`odom_callback`) does not fire during movement.

## Movement Primitives

The higher-level methods are thin wrappers:

```python
def move_dist(self, distance: float):
    seconds = abs(distance) / self.linear
    actual_speed = self.linear if distance >= 0 else -self.linear
    self.cmd_vel_helper(actual_speed, 0.0, seconds)

def turn_amount(self, angle: float):
    seconds = abs(angle) / self.angular
    angular_speed = self.angular if angle >= 0 else -self.angular
    self.cmd_vel_helper(0.0, angular_speed, seconds)

def turn_degrees(self, degrees: float):
    self.turn_amount(math.radians(degrees))
```

Sign conventions: positive distance = forward, positive angle = counterclockwise (ROS standard).

## Odometry Subscription

The subscription stores the latest pose but does not act on it during movement (since `odom_callback` is not serviced during `cmd_vel_helper`). This is a foundation for future closed-loop control:

```python
def odom_callback(self, msg):
    self.current_pose = msg.pose.pose
```

## Observations

- **Open-loop movement.** `move_dist` computes time from speed; it does not use odometry feedback. Wheel slip or hardware variation accumulates as error.
- **Blocking architecture.** `cmd_vel_helper` blocks the calling thread for the full movement duration. No other intents are processed during a turn.
- **Odometry inactive during movement.** Without `spin_once`, `odom_callback` never fires while the robot is moving. Closed-loop control would require a dedicated executor thread.
- **10 Hz fixed rate.** The publish rate is hardcoded. A configurable rate or ROS timer would be more idiomatic.
