# better_launch Cheat Sheet

## Invocation

Prefer `bl`, not `ros2 launch`, for better_launch launch files:

```bash
bl my_package my_launch.launch.py
bl my_package my_launch.launch.py --enable_camera True
bl my_package my_launch.launch.py --robot_namespace robot1
```

Use `ros2 launch` only when you specifically need ROS2 launch compatibility.
better_launch supports it, but `bl` is the native and preferred command.

Use the package form for normal testing and operation:

```bash
bl my_package my_launch.launch.py --enable_camera False
```

This verifies that the launch file is installed and discoverable through the ROS
package index. Direct path launches are useful only for quick local experiments
before install/package discovery matters.

## Python Launch File Shape

Use the standard better_launch pattern:

```python
#!/usr/bin/env python3
from better_launch import BetterLaunch, launch_this


@launch_this(ui=False)
def my_launch(enable_camera: bool = False, use_rviz: bool = True):
    bl = BetterLaunch()

    if enable_camera:
        bl.node("my_package", "camera_node", "camera")

    if use_rviz:
        bl.node("rviz2", "rviz2", "rviz2")
```

Function parameters become launch arguments. Use type hints and defaults so
better_launch parses command-line values into the intended Python types.

## Boolean Arguments

Use normal Python booleans in the launch function:

```python
def my_launch(enable_camera: bool = True, use_rviz: bool = False):
```

Call with capitalized boolean values through `bl`:

```bash
bl my_package my_launch.launch.py --enable_camera False --use_rviz True
```

Do not add custom string coercion for booleans unless there is a concrete
non-`bl` caller that requires it.

## Node Calls

Start nodes with `bl.node(package, executable, name, ...)`.

Use `env={...}` for per-node environment variables:

```python
bl.node(
    "my_package",
    "worker_node",
    "worker",
    env={"MY_SETTING": "value"},
)
```

Use `params={...}` for ROS parameters:

```python
bl.node(
    "my_package",
    "worker_node",
    "worker",
    params={"rate_hz": 10.0, "enabled": True},
)
```

## Including Launch Files

Use `bl.include(package, launch_file, **args)`:

```python
bl.include(
    "other_package",
    "other_launch.launch.py",
    use_sim_time=False,
)
```

## References

- Documentation: https://dfki-ric.github.io/better_launch/
- Repository: https://github.com/dfki-ric/better_launch
