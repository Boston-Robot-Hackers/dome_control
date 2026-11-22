---
version: "1.0"
generated: "2026-11-22"
---

# Appendix X15 — `launch/robot.launch.py`

The robot-side launch file, written with `better_launch` to the DOME launch
convention (dome2 F05 TF05.2):

```python
@launch_this(ui=True)
def robot_launch():
    bl = BetterLaunch()
    bl.node("dome_control", "behavior_manager", "behavior_manager")
    bl.node("dome_control", "telemetry_node", "telemetry")
    bl.node("dome_control", "spin_survey_node", "spin_survey",
            param_files=bl.find("dome_control", "spin_survey.yaml"),
            ros_waittime=10.0)
```

It starts only `dome_control`'s own nodes. `dome2` combines it with other
packages' launch files.

## Observations

- **Two config files hold spin_survey settings, and they disagree.**
  `config/spin_survey.yaml` is the one loaded here (step 0.5 rad, 2
  passes). `config/control-config.yaml` also has a `spin_survey:` block
  (step 0.872 rad, 1 pass) that **no code reads**. Delete the dead block so
  nobody tunes the wrong file.
- **`ros_waittime=10.0`** applies only to `spin_survey`. A one-line comment
  on why would help the next reader.
