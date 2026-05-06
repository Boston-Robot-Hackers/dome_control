#!/usr/bin/env python3
"""
Simple CLI using CommandDispatcher
Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

import control.commands.command_dispatcher as cd
import control.commands.config_manager as cm
import control.commands.robot_controller as rc


class SimpleCLI:

    def __init__(self):
        config_path = os.environ.get("CONTROL_CONFIG", str(Path.home() / ".control" / "config.yaml"))
        self.config_manager = cm.ConfigManager.create(config_path)
        self.robot_controller = rc.RobotController(self.config_manager)
        self.dispatcher = cd.CommandDispatcher(self.robot_controller)
        self.running = True

        # Set up command history with timestamps in control directory
        control_dir = self.config_manager.get_control_dir()
        self.command_history_file = control_dir / "command_history.txt"
        history_file = control_dir / "prompt_history.txt"
        self.prompt_history = FileHistory(str(history_file))

    def _load_help_file(self, filename: str):
        # Resolve symlinks to get actual source directory
        module_path = Path(__file__).resolve()
        docs_dir = module_path.parent.parent.parent / "docs"
        help_file = docs_dir / filename

        if help_file.exists():
            return help_file.read_text()
        return None

    def _show_subcommand_suggestions(self, command_name, header, footer=None):
        suggestions = [
            cmd for cmd in self.dispatcher.commands.keys()
            if cmd.startswith(f"{command_name}.")
        ]
        if not suggestions:
            return False

        print(header)
        for suggestion in sorted(suggestions):
            cmd_def = self.dispatcher.commands[suggestion]
            subcommand = suggestion.split(".", 1)[1]
            print(f"  {command_name} {subcommand:<20} - {cmd_def.description}")
        if footer:
            print(footer)
        return True

    def _show_common_commands(self):
        print("Common Commands:")
        print()
        print("Movement:")
        print("  move forward <meters>")
        print("  move backward <meters>")
        print("  turn clockwise <degrees>")
        print("  turn counterclockwise <degrees>")
        print()
        print("Control:")
        print("  robot stop")
        print("  robot status")
        print()
        print("Configuration:")
        print("  config get <variable>")
        print("  config set <variable> <value>")
        print()
        print("Launch:")
        print("  launch start <type>")
        print("  launch stop <type>")
        print()
        print("Scripts:")
        print("  script square --meters <value>")
        print()
        print("Other:")
        print("  help <command>        - Show help for specific command")
        print("  help commands         - Show all available commands")
        print("  exit                  - Exit the program")

    def _show_all_commands(self):
        print("All Available Commands (alphabetical):")
        print("=" * 70)
        for cmd_name in sorted(self.dispatcher.commands.keys()):
            cmd_def = self.dispatcher.commands[cmd_name]
            display_name = cmd_name.replace(".", " ")
            print(f"  {display_name:<30} - {cmd_def.description}")
        print("\nFor detailed help on any command: help <command> <subcommand>")

    def _show_specific_help(self, parsed: ParsedCommand):
        if parsed.arguments:
            filename = f"{parsed.subcommand}.{parsed.arguments[0]}.txt"
        else:
            filename = f"{parsed.subcommand}.txt"

        help_text = self._load_help_file(filename)
        if help_text:
            print(help_text)
            return

        command_name = parsed.subcommand
        found = self._show_subcommand_suggestions(
            command_name,
            f"Available '{command_name}' commands:",
            f"\nFor detailed help, use: help {command_name} <subcommand>"
        )
        if not found:
            command_str = (
                f"{parsed.subcommand} {parsed.arguments[0]}"
                if parsed.arguments
                else parsed.subcommand
            )
            print(f"No help available for: {command_str}")

    def _handle_help(self, parsed: ParsedCommand):
        if parsed.arguments and len(parsed.arguments) == 1 and parsed.arguments[0] == "commands":
            self._show_all_commands()
            return

        if parsed.subcommand:
            self._show_specific_help(parsed)
        else:
            self._show_common_commands()


    def execute_command(self, input_text: str):
        if not input_text.strip():
            return

        tokens = input_text.strip().split()
        first = tokens[0].lower()

        if first in ("help", "hlp"):
            from control.commands.command_dispatcher import resolve_keyword
            # Reconstruct minimal parsed structure for help handler
            class _P:
                pass
            p = _P()
            p.command = "help"
            p.subcommand = resolve_keyword(tokens[1]) if len(tokens) > 1 else None
            p.arguments = [resolve_keyword(t) for t in tokens[2:]]
            self._handle_help(p)
            return

        if first in ("exit", "quit", "q", "x"):
            print("Goodbye!")
            self.running = False
            return

        result = self.dispatcher.dispatch_text(input_text)

        if result.success:
            print(f"✓ {result.message}")
            if result.data:
                self._print_data(result.data)
        else:
            print(f"✗ {result.message}")
            command_name = tokens[0]
            if "Unknown command" in result.message and "." not in command_name:
                self._show_subcommand_suggestions(
                    command_name,
                    "Did you mean one of these?"
                )

    def _print_data(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                elif isinstance(value, list):
                    print(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"{key}: {value}")
        else:
            print(data)

    def _log_command(self, command: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        with open(self.command_history_file, "a") as f:
            f.write(f"\n# {timestamp}\n")
            f.write(f"+{command}\n")

    def repl(self):
        print("Robot Control CLI (Simple Parser)")
        print("Type 'help' for available commands, 'exit' to quit")
        print()

        while self.running:
            try:
                # Read command with history support
                input_text = prompt("robot> ", history=self.prompt_history)

                # Skip empty commands
                if not input_text.strip():
                    continue

                # Log command to file
                self._log_command(input_text.strip())

                # Execute command
                self.execute_command(input_text)

            except EOFError:
                # Ctrl+D
                print()
                print("Goodbye!")
                self.running = False
            except KeyboardInterrupt:
                # Ctrl+C
                print()
                print("Use 'exit' to quit")



def main():
    cli = SimpleCLI()

    if len(sys.argv) > 1:
        # Non-interactive: execute command from args
        command = " ".join(sys.argv[1:])
        cli.execute_command(command)
    else:
        # Interactive REPL
        cli.repl()


if __name__ == "__main__":
    main()
