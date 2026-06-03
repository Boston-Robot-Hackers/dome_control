# I10 Codebase-wide style drift; no lint gate enforcing codereview rules

* **Symptom**: Several `codereview.md` MUST/SHOULD rules are violated broadly in
  older code:
  - Leading underscores on identifiers (`codereview.md:80`): e.g.
    `_load_launch_configs`, `_capture_output`, `_format_launch_params`
    (`ros2_api/process_api.py`), `_validate_config` (`ros2_api/movement_api.py`),
    `_print_elapsed_time` (`ros2_api/calibration_api.py`), `_format_table_row`
    (`interface/simple_cli.py`), `SurveyApi._client`.
  - Old typing `Optional/Dict/List` in `ros2_api/process_api.py:9` (rule bans
    `Optional`); rest of the code uses `X | None`, `dict`, `list`.
  - Missing file headers (Author/MIT, a MUST) in `base_api.py`, `movement_api.py`,
    `process_api.py`, `intent_api.py`.
* **Tests done**: Code read; nothing enforces these (no `test_flake8.py`; `setup.cfg`
  only ignores `Q000`).
* **Latest theory**: One mechanical cleanup pass, then add ament_flake8 (and the
  pytest suite) to a lint/CI gate so the rules stay enforced. Large but low-risk.
