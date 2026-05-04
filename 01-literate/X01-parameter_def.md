---
version: "1.0"
generated: "2026-05-04"
---

# Parameter Definition (Appendix)

`parameter_def.py` defines a single dataclass describing one parameter a command can accept.

```python
@dataclass
class ParameterDef:
    name: str           # kwarg name passed to RobotController method
    param_type: type    # e.g. float, bool, str — used for coercion
    required: bool      # if True, dispatcher raises ValueError when absent
    default: object     # None means "no default" (not the same as required=False)
    description: str    # shown in help text
```

`param_type` is the type itself (e.g. `float`), not a string, so `CommandDispatcher` can call `param_type(value)` directly. `bool` needs a special branch because `bool("false") == True`.

No business logic. No imports beyond stdlib. Everything else depends on this.
