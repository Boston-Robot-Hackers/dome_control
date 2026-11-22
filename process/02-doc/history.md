# control — History

Completed checkpoints moved out of `current.md`. Newest first.

## 2026-11-22 — `.claude/` kit sync and `process/` move (chore)

- `.claude/` re-synced from the canonical `~/j3/.claude` kit: new agents
  (explorer/reviewer/architect), hooks (block-secrets, post-edit ruff,
  session-start), `/feature` and `/close-feature`, style guide v4.4, and the
  newer `process.md` rules. `settings.local.json` kept local.

- `01-literate/`–`05-issues/` moved under `process/` with `git mv`, matching
  the kit and the sibling repos. Every doc cross-reference re-pointed,
  `done/` files included.

- Adapted for this repo: `uv run` → plain `ruff` / `python3 -m pytest test/`
  (no `uv` on the robot), `settings.json` `autoMode` filled in, `CLAUDE.md`
  rewritten from the new template.

- `current.md` restructured to the new format (only `## Open`, opening with
  `### Pick up here`); "What Is Built", config, lint and commands moved to
  `notes.md`, and its stale UPS-direct-read note fixed for F20.

- 217 tests passing (workspace must be sourced).

## 2026-11-19 — ruff cleanup (chore)

- Added `ruff.toml` (line length 88, `EXE001` ignored, same as dome_mission)
  and brought the repo from 131 violations to zero: autofixes (import order,
  unused imports, PEP 585/604 annotations), `ruff format` across code and the
  Python blocks in Markdown, and hand fixes.

- `process_api.py`: every `except Exception` narrowed to the errors actually
  raised (`OSError`, `ValueError` on a closed pipe); the bare `except: pass`
  around `stdout.close()` removed; `_capture_output` split into
  `stream_output` / `write_log_header` / `write_log_footer` with the log file
  opened via `with`. New `test/test_process_api_capture.py` (3 tests).

- `RobotController.list_topics` lost its redundant catch-all; the dispatcher
  is the single CLI error boundary.

## 2026-11-19 — dome2 F05 launch cleanup, dome_control part

- **TF05.2** (`9046e75`): `launch/robot.launch.py` now follows the DOME launch
  convention (header, usage examples, argument docstrings). spin_survey's
  inline params moved to `config/spin_survey.yaml` with the same values, plus
  `test/test_spin_survey_params.py` checking its keys match
  `SpinSurveyConfig`. Added the header-stamping `.githooks/pre-commit`.

- **TF05.3** (`6f42ffd`): deleted the empty `launch/remote.launch.py`.

- **Clean stop** (`3cc2873`): nodes exit cleanly on
  `ExternalShutdownException` when a launch is stopped.

- The feature and task records live in dome2:
  `dome2/process/03-features/notdone/F05-launch-file-cleanup.md`.

## 2026-08-07 — F20 merged, F22 closed

- **F22** (`robot subsystems` status command): `ProcessApi.get_subsystem_status()`
  + `get_mission_state()`, `RobotController.get_subsystems_status()`,
  `robot.subsystems` CLI table, `dome_mission`'s `/mission/state` publisher.
  T06 verified on `dome-R1`: all six subsystems plus mission FSM state.

- **F20** merged: battery telemetry moved to the sibling `dome_telemetry`
  package (verified on the live robot 2026-08-04). Its code had been
  stranded on an unmerged worktree branch until this merge.

- Control config moved from `~/.control/config.yaml` to
  `~/.dome/config/control.yaml`; `CONTROL_CONFIG` env var dropped.

## 2026-08-05 — F21 closed

- `nav` CLI domain renamed to `mission` (`mission.go.start/stop`,
  `mission.explore.start/stop/status`).

- `navigation_commands.py` split into `map_commands.py` +
  `mission_commands.py`. `cli-reference.md` and `docs/launch.start.txt`
  updated.
