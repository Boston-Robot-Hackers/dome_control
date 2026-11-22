---
version: "1.0"
generated: "2026-05-13"
---

# Module Entry Point: `__main__.py`

## Purpose

`__main__.py` makes the `dome_control` package directly runnable via
`python3 -m dome_control`. It owns the top-level lifecycle: initialize
`rclpy`, run the CLI, and shut down cleanly regardless of how the CLI exits.

## Design

The file is intentionally minimal. All CLI logic lives in
`dome_control.interface.simple_cli`; all ROS2 node logic lives deeper in
the package. This module's only responsibility is to bracket the CLI call
with `rclpy.init()` / `rclpy.shutdown()`.

```python
#!/usr/bin/env python3
import rclpy
import dome_control.interface.simple_cli as cli


def main():
    rclpy.init()
    try:
        cli.main()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
```

The `try/finally` guarantees `rclpy.shutdown()` runs even if `cli.main()`
raises — preventing resource leaks in the underlying ROS2 middleware.

## Observations

- No issues. File is appropriately thin.
- `rclpy.init()` here means no test can import this module without a live
  ROS2 environment. Tests should import `simple_cli` directly, not
  `__main__`, which is already the pattern used in this repo.
