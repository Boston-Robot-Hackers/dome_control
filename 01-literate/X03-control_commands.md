---
version: "1.0"
generated: "2026-05-04"
---

# Control Commands (Appendix)

`control_commands.py` defines two basic robot control commands.

```python
"robot.stop":   CommandDef("stop_robot",       [], "Stop robot movement",     group="control")
"robot.status": CommandDef("get_robot_status", [], "Get current robot status", group="control")
```

Neither command takes parameters. `robot.stop` publishes a zero-velocity Twist via `MovementApi`. `robot.status` returns a structured status dict including speed config, tracked launch process PIDs, and which API nodes are initialised.
