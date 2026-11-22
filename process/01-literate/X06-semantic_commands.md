---
version: "2.0"
generated: "2026-05-06"
status: "removed"
---

# Semantic Commands (Removed in F15/T07)

`semantic_commands.py` defined user-friendly aliases (`scene.describe`, `scene.count`) that mapped to the same `RobotController` methods as the `intent.*` commands. These were entries in the `CommandDispatcher` registry.

The file was deleted in F15/T07. The `scene.*` aliases survive as entries in `BEHAVIOR_COMMANDS` in `command_dispatcher.py`, routed by `dispatch_text`.

See `12-command_dispatcher.md` for the current routing mechanism.
