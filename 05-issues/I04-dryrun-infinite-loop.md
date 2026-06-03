# I04 Stress-test loops spin at 100% CPU in dry-run

* **Symptom**: `run_rotate_stress` / `run_circle_stress` loop `while rclpy.ok()`
  (`ros2_api/calibration_api.py:62,102`). In dry-run, `cmd_vel_helper` returns
  immediately (`ros2_api/movement_api.py:126`), so the inner work is instant and the
  outer `while` becomes a tight infinite loop with no sleep. Because
  `detect_test_environment` forces `dry_run=True` under pytest
  (`commands/config_manager.py:91`), any test that calls these hangs the suite.
* **Tests done**: Code read; not yet hit because no test calls the stress methods.
* **Latest theory**: Guard the loop body with a dry-run short-circuit (log once and
  return) and/or add a minimum cycle sleep. Related to the dry-run heuristic in I07.
