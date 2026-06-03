# I13 Spec/overview describe an architecture the code no longer has

* **Symptom**: The design docs can't be trusted as intent for the command layer
  because they describe a prior design:
  - `spec.md:16` names `interface/SimpleCommandParser` — no such module exists
    (only `interface/simple_cli.py`).
  - `01-literate/00-overview.md:89-100` documents a `BaseCommand →
    MovementCommand / LaunchCommand / SystemCommand / NavigationCommand /
    IntentCommand` dataclass hierarchy. The code instead uses `CommandDef` +
    `ParameterDef` + `build_*_commands()` builder functions
    (`commands/command_def.py`, `commands/*_commands.py`); there is no `BaseCommand`
    hierarchy.
* **Tests done**: Code read vs. docs; the named symbols/classes are absent.
* **Latest theory**: Reconcile the docs to the real `CommandDef`/dispatcher design
  (or vice-versa if the hierarchy is still wanted). Until then, intent-based reviews
  of the command layer must read the code, not the overview. Relates to I14.
