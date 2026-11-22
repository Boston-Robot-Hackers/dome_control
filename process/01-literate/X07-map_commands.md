---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X07 — map command table

`commands/map_commands.py` defines the `map` group:

- **`map save`**: `map_saver_cli` writes `<map_name>.yaml` and `.pgm`.
- **`map serialize`**: the SLAM Toolbox `serialize_map` service writes
  `.posegraph` and `.data`.
- **`map list`**: groups files in `~/.dome/config/maps` by stem.

`save` and `serialize` take no arguments. They read the `map_name` config
variable, so the workflow is `config set map_name kitchen` then `map save`.

## Observations

- **Pass the name as an argument.** An optional argument
  (`map save [name]`, defaulting to `map_name`) removes a hidden two-step
  dependency.
- **The paths go into shell strings unquoted.** `map_serialize` builds
  `"{filename: '<path>'}"` inside a `shell=True` command, so a map name
  with a space or quote breaks it. Use `shlex.quote`, or call the service
  through rclpy.
- **Who owns maps?** SLAM and maps belong to `dome_nav` now. It's worth
  deciding whether these commands stay in the control CLI or call a
  `dome_nav` service.
