# I07 dry_run auto-enabled by sniffing sys.modules

* **Symptom**: The robot can silently refuse to move. `detect_test_environment`
  sets `dry_run=True` whenever `"pytest"` or `"unittest"` is in `sys.modules`
  (`commands/config_manager.py:91`). `unittest` is imported transitively by many
  libraries, so a production process can trip this and go into dry-run unexpectedly.
* **Tests done**: Code read only.
* **Latest theory**: Replace the heuristic with an explicit signal — env var
  (e.g. `CONTROL_DRY_RUN`) or a pytest fixture that sets `dry_run` deliberately.
  Also the root cause behind I04 being able to hang the suite.
