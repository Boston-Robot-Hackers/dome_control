# I11 Misc consistency cleanups (logging, returns, imports, duplicated coercion)

* **Symptom**: Smaller inconsistencies that bite over time:
  - `base_api.log_info` uses bare `print()` (`ros2_api/base_api.py:28`) while
    `log_debug/warn/error` use the ROS logger — console output bypasses levels.
  - `RobotController.turn_radians` returns a `CommandResponse` (`:312`) but
    `turn_degrees` returns the raw `None` from `movement.turn_degrees` (`:317`).
  - `make_announcement_msg` imported from `announcement_contract` in
    `motion_behavior.py:8` but from `intent_parser` (a re-export) in
    `perception_behavior.py:8`.
  - Numeric coercion reimplemented three times: `ConfigManager.convert_number`,
    `command_dispatcher.parse_value`, `telemetry/config.positive_*` (see I06).
  - Bare `except:` swallowing all errors at `ros2_api/process_api.py:422`.
* **Tests done**: Code read only.
* **Latest theory**: Pick one convention each (logger for info; methods return
  `CommandResponse`; one import path; one shared coercion helper; specific excepts)
  and apply. Low risk, improves grep-ability and testing.
