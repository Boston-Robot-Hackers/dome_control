---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X01 — ParameterDef

`commands/parameter_def.py` declares one CLI command parameter:

```python
@dataclass
class ParameterDef:
    name: str
    param_type: type
    required: bool
    default: object
    description: str
```

The dispatcher uses `param_type` to convert the token, `required` to
reject missing arguments, and `default` to fill optional ones. Parameters
are positional: the order in the `CommandDef` list is the order the user
types them.

## Observations

- **Every table passes five positional arguments**, as in
  `ParameterDef("meters", float, True, None, "Distance in meters")`. That
  reads poorly, and `True, None` is easy to swap. Keyword arguments or
  defaults (`required=True`, `default=None`) would shorten the tables.
- **`default=None` means "no default"**, so `None` itself can never be a
  default. That's fine today, but worth knowing.
- **Use `frozen=True`.** Definitions are static and should be immutable.
