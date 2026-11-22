---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X05 — system, config and script command table

`commands/system_commands.py` covers three groups:

- **`script`**: `list`, `square <m>`, `rotate_stress`,
  `circle_stress <diameter>`, all in `CalibrationApi`.
- **`config`**: `set <name> <value>`, `get <name>`, `list`, all in
  `ConfigManager`.
- **`system`**: `topics`, `ps`, `kill <pid>`, `launches`, all in
  `ProcessApi`.

## Observations

- **The module holds three unrelated groups.** It would be clearer split
  into `script_commands.py`, `config_commands.py` and
  `system_commands.py`, matching the other one-group-per-file tables.
- **`script circle_stress` doesn't honour its diameter** (see
  `06-calibration_api.md`).
- **`config set`'s value is declared `str`**, but the dispatcher has
  already turned `"1"` into `True` before conversion. That is the
  `config.set` chore (see `11-command_dispatcher.md`).
- **`script list` duplicates this table.** It returns a hand-written dict
  of script descriptions instead of reading this table.
