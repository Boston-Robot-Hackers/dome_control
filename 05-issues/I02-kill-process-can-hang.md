# I02 kill_process can hang indefinitely on stop

* **Symptom**: Stopping a launch can block the CLI forever.
  `kill_process` sends SIGINT then calls `communicate()` with no timeout
  (`ros2_api/process_api.py:310`). Processes are started with
  `start_new_session=True` (`:261`), so SIGINT reaches the shell leader but
  grandchildren can keep the pipe open; `communicate()` then never returns. There
  is no SIGKILL fallback here (unlike `kill_ros_process` at `:430`).
* **Tests done**: Code read only.
* **Latest theory**: Signal the whole process group (negative PID), add
  `communicate(timeout=...)`, and escalate SIGINT → SIGTERM → SIGKILL on timeout.
  Reuse the group-leader detection already in `kill_ros_process`. Fix with I01.
