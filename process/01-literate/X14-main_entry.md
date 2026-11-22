---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X14 — CLI entry points (`main.py`, `__main__.py`)

Both files hold the same 17 lines:

```python
def main():
    rclpy.init()
    try:
        cli.main()
    finally:
        rclpy.shutdown()
```

- `main.py` backs `scripts/run`, which is what `ros2 run dome_control run`
  executes.
- `__main__.py` backs `python3 -m dome_control`.

`rclpy` is initialised once here, so `SimpleCLI` and every API node it
creates share one context. The `finally` makes sure the context is shut
down even when the REPL raises.

## Observations

- **The two files are duplicates.** Make `__main__.py` a two-line
  `from dome_control.main import main; main()`.
- **Nodes are never destroyed.** `rclpy.shutdown()` tears down the context,
  but the controller's nodes are never `destroy_node()`d first (I05), so
  `ProcessApi`'s "kill managed processes on shutdown" never runs.
