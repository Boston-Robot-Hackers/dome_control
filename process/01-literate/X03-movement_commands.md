---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X03 — movement command table

`commands/movement_commands.py` defines the `move.*` and `turn.*`
commands:

| Command | Method | Argument |
|---|---|---|
| `move time` | `move_for_time` | seconds |
| `move forward` / `backward` | `move_forward` / `move_backward` | meters |
| `turn time` | `turn_for_time` | seconds |
| `turn radians` | `turn_radians` | radians (signed, + = CCW) |
| `turn clockwise` / `counterclockwise` | `turn_*` | degrees |

The sign conventions differ. `turn clockwise 90` and `turn
counterclockwise 90` take magnitudes, and the controller applies the sign.
`turn radians` passes its signed value straight to `MovementApi`.

## Observations

- **Units are inconsistent.** Degrees and radians both appear, and `move
  time`/`turn time` take no speed. Choosing degrees for all user-facing
  angles would simplify the table. `turn radians` is useful mainly for
  calibration.
- **Durations and distances aren't range-checked here.** Negative values
  reach `MovementApi`, which handles them unevenly (see
  `05-movement_api.md`).
