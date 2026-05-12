---
version: "1.1"
generated: "2026-05-12"
---

# BaseApi

`base_api.py` defines the abstract base class shared by all ROS2 API nodes in this package. It is the point where ROS2's `Node` machinery meets the package's configuration and logging conventions.

## Multiple Inheritance

```python
class BaseApi(Node, ABC):
    def __init__(self, node_name: str, config_manager: cm.ConfigManager = None):
        super().__init__(node_name)
        self.config = config_manager
```

`BaseApi` inherits from both `Node` (ROS2) and `ABC` (Python abstract base class). The `ABC` inheritance isn't strictly necessary here — there are no `@abstractmethod` declarations — but it signals that `BaseApi` is not meant to be instantiated directly.

`config_manager` may be `None`. Callers that need config pass it explicitly. In production all API nodes receive the same `ConfigManager` instance from `RobotController`, which is important for shared state (e.g., `dry_run` flag, speed variables).

## Logging Conventions

Four logging methods wrap ROS2's logger with a twist:

```python
def log_debug(self, message: str):
    self.get_logger().debug(message)

def log_info(self, message: str):
    print(message)          # ← goes to stdout, not ROS2 log

def log_warn(self, message: str):
    self.get_logger().warn(message)

def log_error(self, message: str):
    self.get_logger().error(message)
```

`log_info` routes to `print()` rather than the ROS2 logger. This is intentional: the CLI user sees stdout directly in their terminal; ROS2 info-level log output typically goes to a separate log sink and isn't visible interactively. `debug`, `warn`, and `error` use the ROS2 logger so they appear in `ros2 topic echo /rosout` and log files.

## Bounds Checking

```python
def check_bounds(self, value: float, min_val: float, max_val: float, name: str) -> bool:
    if not (min_val <= value <= max_val):
        self.log_warn(f"{name} out of bounds: {value}. Must be [{min_val}, {max_val}]")
        return False
    return True
```

This helper is used by `MovementApi.check_velocity_limits` before every velocity command. Keeping it in `BaseApi` makes it available to any future API class that also needs range validation.

## Node Lifecycle

`destroy_node` overrides the ROS2 default to log a shutdown message before calling `super().destroy_node()`. This gives a consistent teardown trace in logs when the CLI exits.

## Observations

- `config_manager` is stored as-is (may be `None`). Subclasses that access `self.config` without checking for `None` will crash if called without a config. Callers that don't need config (e.g. `IntentApi`) pass `None` safely as long as they don't call config-dependent methods.
- `ABC` is imported but not used for its primary purpose. Future API classes that must implement specific methods could use `@abstractmethod` here.
