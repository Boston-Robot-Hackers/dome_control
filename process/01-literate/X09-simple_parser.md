---
version: "2.0"
generated: "2026-05-06"
status: "removed"
---

# SimpleCommandParser (Removed in F15/T05)

`simple_parser.py` was the text-to-command parser for the CLI. It converted free-form strings into `ParsedCommand` objects. The file was deleted in F15/T05.

## What Replaced It

`CommandDispatcher.dispatch_text(text)` absorbed all functionality:

- Abbreviation resolution (`ABBREV_TO_FULL`, `FULL_NAMES`, `resolve_keyword`)
- Subcommand detection (checks `FULL_NAMES`, abbreviation expansion, and command registry)
- Value type inference (`parse_value`: bool → int → float → str)

`SimpleCLI.execute_command` now calls `dispatcher.dispatch_text(input_text)` directly. The intermediate `_map_to_dispatcher_format` step was also removed.

See `12-command_dispatcher.md` for the current implementation.
