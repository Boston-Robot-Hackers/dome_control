---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X09 — survey command table

`commands/survey_commands.py` defines one command, `survey start`, which
calls `RobotController.start_survey`, then `SurveyApi`, then the
`/survey/start` service on `spin_survey_node`.

## Observations

- **Add `survey stop`** once the node has a cancel service (see
  `17-spin_survey_node.md`). Today a running survey can't be stopped from
  the CLI.
- **The file header lacks the stamped fields.** It has no
  `Version`/`Created`/`Updated` lines, which the pre-commit hook adds on
  the next change.
