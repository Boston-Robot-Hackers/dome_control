---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X04 — launch command table

`commands/launch_commands.py` defines `launch list`, `launch info <type>`,
`launch start <type> [use_sim_time] [map] [map_name]` and `launch stop
<type>`. They map onto `RobotController.launch_*`, which wraps
`ProcessApi`'s template launcher (see `07-process_api.md`).

## Observations

- **The help text promises flags that don't exist.** Descriptions mention
  `--use-sim-time` and `--map-name`, but the dispatcher has no flag
  syntax; parameters are positional. This is the stale `--flag` syntax
  noted in `process/02-doc/cli-reference.md` and the README chore.
- **The type examples are stale.** "(nav, slam, map)" is hard-coded. The
  real types are whatever `launch_templates:` holds. `launch list` is the
  source of truth.
- **`map` and `map_name` overlap.** Both name a map file, and they are
  resolved differently in `launch_by_type`. One parameter would do.
