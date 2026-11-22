---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X08 — mission command table

`commands/mission_commands.py` is the CLI face of `dome_mission` (F19,
renamed from `nav` in F21):

| Command | Publishes intent | Owner |
|---|---|---|
| `mission go start <label>` | `navigation_go {label}` | dome_mission |
| `mission go stop` | `navigation_cancel` | dome_mission |
| `mission explore start` | `exploration_start` | dome_mission |
| `mission explore stop` | `exploration_stop` | dome_mission |
| `mission explore status` | reads `/explore/status` | dome_nav's explore manager |

These are three-word commands. The dispatcher's three-token lookup exists
for them.

The publish commands go through `RobotController.publish_intent_*`, that
is, the controller's own `IntentApi`, rather than the dispatcher's
behavior path. So they are fire-and-forget, and none of them waits for a
reply.

## Observations

- **Use the behavior path.** As behavior commands with real `CommandDef`s
  (see `11-command_dispatcher.md`), these would use the dispatcher's
  shared publisher and drop four one-line controller methods.
- **The two stops are separate on purpose (F19).** `mission go stop` and
  `robot stop` don't know about each other. Say so in the descriptions,
  so a user doesn't expect `robot stop` to cancel navigation.
- **`explore status` shells out** to `ros2 topic echo`. See
  `10-robot_controller.md`.
