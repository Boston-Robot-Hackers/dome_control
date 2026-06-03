# I14 CLI command parsing is inconsistent in both syntax and implementation

* **Symptom**: Multiple parsers and coercion rules disagree, producing surprises.

  **Implementation split (several parsers for one job):**
  - `interface/simple_cli.py:184` tokenizes input itself (`.strip().split()`,
    `.lower()`) to peel off `help`/`exit` before handing the *raw* text to
    `CommandDispatcher.dispatch_text`, which tokenizes *again* with `shlex`
    (`commands/command_dispatcher.py:195`). Two tokenizers, different rules.
  - `exit`/`quit`/`q`/`x` are handled in the CLI (`simple_cli.py:193`) *and* mapped
    in `ABBREV_TO_FULL` (`command_dispatcher.py:32`) — double handling.
  - Value coercion is implemented three times with different rules:
    `parse_value` (`command_dispatcher.py:43`), `ConfigManager.convert_number` /
    `set_variable` (`config_manager.py:36-50`), and `telemetry/config.positive_*`.

  **Concrete bug from that split:** `parse_value("1")` returns `True` and
  `parse_value("0")` returns `False` (verified). So `config set foo 1` flows
  `"1" → True → str(True) = "True" → ConfigManager stores boolean True`. Setting a
  config var to `1`, `0`, `yes`, `no` silently stores a boolean, not the literal.

  **Syntax inconsistency:** some commands are flat (`help`, `exit`), most are dotted
  two-word (`move forward`, `config set`, `system kill`, `scene describe`); the
  dotted-vs-flat decision is a heuristic
  (`command_dispatcher.py:210`: `second in FULL_NAMES or second != tokens[1] or
  in_registry`) that can misread a bare command whose string argument happens to be
  a known keyword. Args are positional-only with a one-off "join trailing tokens if
  last param is str" special case (`:235`). Abbreviations are an ad-hoc flat map
  mixing command and subcommand names, only covering some commands.

* **Tests done**: `parse_value` behavior confirmed via direct call; the rest by
  reading the two parse paths.
* **Latest theory**: One tokenizer + one grammar + one coercion function, with a
  single place that decides command vs subcommand vs args. Make `parse_value`
  context-aware (don't bool-coerce values destined for `str`/numeric params), or
  defer all coercion to the per-parameter `ParameterDef` type. Relates to I06
  (duplicate numeric coercion) and I13 (the documented parser doesn't exist).
