---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X02 — CommandDef

`commands/command_def.py` is one registry entry:

```python
@dataclass
class CommandDef:
    method_name: str
    parameters: list[pd.ParameterDef]
    description: str
    group: str
```

- **`method_name`** is looked up with `getattr` on `RobotController` at
  call time, so a typo is only found when the command runs ("Method X not
  found").
- **`group`** drives `help` grouping.

Behavior commands are registered with `method_name=""` and no parameters
(see `11-command_dispatcher.md`).

## Observations

- **Add an `intent_name: str | None` field** so behavior commands can be
  first-class entries with real parameters, instead of a side table plus
  empty placeholders.
- **Check method names at startup.** A test that every `method_name`
  exists on `RobotController` would catch typos in CI.
- **Use `frozen=True`**, as for `ParameterDef`.
