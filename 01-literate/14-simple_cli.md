---
version: "1.0"
generated: "2026-05-04"
---

# SimpleCLI

`simple_cli.py` is the top-level entry point for the robot control CLI. It assembles the full stack — config, controller, dispatcher, parser — and provides both an interactive REPL and a non-interactive single-command mode.

## Assembly at Startup

```python
class SimpleCLI:
    def __init__(self):
        self.parser = SimpleCommandParser()
        config_path = os.environ.get("CONTROL_CONFIG", str(Path.home() / ".control" / "config.yaml"))
        self.config_manager = cm.ConfigManager.create(config_path)
        self.robot_controller = rc.RobotController(self.config_manager)
        self.dispatcher = cd.CommandDispatcher(self.robot_controller)
```

Construction order matters: `ConfigManager` → `RobotController` → `CommandDispatcher`. The config must exist before the controller initialises (it reads launch templates), and the controller must exist before the dispatcher (it needs a controller to dispatch to).

`CONTROL_CONFIG` environment variable allows pointing to a non-default config file, useful for running with a test config or a different robot profile.

## Two Modes

```python
def main():
    cli = SimpleCLI()
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        cli.execute_command(command)
    else:
        cli.repl()
```

Non-interactive mode: `ros2 run control run move forward 1.0` — the CLI executes one command and exits. Useful for scripting and testing.

Interactive REPL: uses `prompt_toolkit` for readline-style history with persistence to `~/.control/prompt_history.txt`. Every command typed is also logged with a timestamp to `~/.control/command_history.txt`.

## Parsing → Dispatcher Mapping

```python
def _map_to_dispatcher_format(self, parsed: ParsedCommand):
    if parsed.subcommand:
        command_name = f"{parsed.command}.{parsed.subcommand}"
    else:
        command_name = parsed.command

    cmd_def = self.dispatcher.get_command_info(command_name)
    params = {}
    for i, arg in enumerate(parsed.arguments):
        if i < len(cmd_def.parameters):
            params[cmd_def.parameters[i].name] = arg

    return command_name, params
```

Positional arguments from the parser are mapped to named parameters using the `ParameterDef` list order. If the user provides more arguments than the command has parameters, the extra arguments are silently dropped.

## Help System

The CLI has a three-tier help system:

```
help                → _show_common_commands()   (curated list of frequent commands)
help commands       → _show_all_commands()       (full alphabetical registry dump)
help <group>        → _show_subcommand_suggestions()  (all commands in that group)
help <group> <sub>  → _load_help_file()          (detailed text file from docs/)
```

Detailed help files are loaded from a `docs/` directory relative to the package source. If the file doesn't exist, the CLI falls back to listing group subcommands.

## Error Feedback

When an unknown command is typed, the CLI tries to be helpful:

```python
if "Unknown command" in result.message and "." not in command_name:
    self._show_subcommand_suggestions(command_name, "Did you mean one of these?")
```

If the user typed a valid group name with no subcommand (e.g., `move` alone), it lists all `move.*` commands. This reduces the need to consult help text for the common case of forgetting a subcommand.

## Observations

- `_log_command` writes to a file on every keypress in the REPL. There is no buffering or rotation — the history file will grow indefinitely.
- The help file loading (`_load_help_file`) resolves the package path via `Path(__file__).resolve()` and traverses up three levels. This is brittle to package layout changes.
- Empty input is silently ignored (`if not input_text.strip(): return`). This is correct behaviour for the REPL but means non-interactive mode with an empty argument string exits silently with no feedback.
