---
version: "1.0"
generated: "2026-05-04"
---

# Command Definition (Appendix)

`command_def.py` defines a single dataclass describing one entry in the command registry.

```python
@dataclass
class CommandDef:
    method_name: str              # method to call on RobotController
    parameters: list[ParameterDef]  # ordered — position maps to CLI arg position
    description: str              # shown in help text
    group: str                    # e.g. "movement", "launch", "config"
```

`method_name` decouples the CLI command name from the Python method name. The ordering of `parameters` is load-bearing: `SimpleCLI._map_to_dispatcher_format` maps CLI positional args to parameter names by index.

No business logic. No imports beyond `parameter_def`.
