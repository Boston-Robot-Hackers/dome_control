---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X06 — robot control command table

`commands/control_commands.py` defines the `robot.*` group:

| Command | Method | What it does |
|---|---|---|
| `robot stop` | `stop_robot` | one zero `Twist` on `/cmd_vel` |
| `robot status` | `get_robot_status` | configured speeds, tracked launches, created API nodes |
| `robot speak <text>` | `speak_text` | publish `/announcement` at chit-chat priority |
| `robot subsystems` | `get_subsystems_status` | `ps` scan per subsystem, plus `/mission/state` |

## Observations

- **`robot stop` is not an emergency stop.** It publishes once. Any other
  `/cmd_vel` publisher (a survey, Nav2, another CLI's move) overrides it
  on its next message. Its description, "Stop robot movement", promises
  more than that.
- **`robot speak` can be mistaken for a query reply.** It shares
  `/announcement` with replies, so a `robot speak` during another CLI's
  5 s reply wait becomes that query's "answer" (see `08-intent_api.md`).
