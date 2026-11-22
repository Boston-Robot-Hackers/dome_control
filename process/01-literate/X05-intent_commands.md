---
version: "2.0"
generated: "2026-05-06"
status: "removed"
---

# Intent Commands (Removed in F15/T07)

`intent_commands.py` defined CLI commands that published to `/intent` via `RobotController` methods (`publish_intent_stop`, `publish_intent_explore`, etc.). These were entries in the `CommandDispatcher` registry.

The file was deleted in F15/T07. Intent routing now lives in `BEHAVIOR_COMMANDS` in `command_dispatcher.py`, handled by `dispatch_text` without going through the registry. `IntentPublisher` replaced the `RobotController` intent methods.

See `12-command_dispatcher.md` for the current routing mechanism.
