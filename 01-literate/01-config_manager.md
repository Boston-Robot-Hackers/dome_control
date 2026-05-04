---
version: "1.1"
generated: "2026-05-04"
---

# ConfigManager: Persistent Configuration for the Robot

Every robot needs a place to live its settings — speed limits, directory paths, launch templates, and runtime flags. `ConfigManager` is that place. It is the first dependency of almost every other module in the stack, which is why it sits at the top of the reading order.

## The Factory Pattern for Safe Initialization

Python constructors cannot return errors, so a direct `__init__` that opens a file is hard to test and hard to reason about. `ConfigManager` solves this with a class-method factory:

```python
@classmethod
def create(cls, config_file: str) -> "ConfigManager":
    manager = cls(config_file)
    manager.load_config()
    manager.ensure_subdirs()
    manager.detect_test_environment()
    return manager
```

`create` sequences the steps that must happen before the object is usable: load the YAML, create missing directories, and detect if we are running under pytest. Callers always use `create`; the constructor is intentionally bare — just stores paths and initializes `variables` to an empty dict.

## Variables as a Typed Dictionary

All configuration lives in a single flat dict `self.variables`, loaded from YAML. The smart part is `set_variable`, which coerces string input to the right Python type before storing:

```python
def set_variable(self, name: str, value: object):
    if not isinstance(value, str):
        self.variables[name] = value
    elif value.lower() in ["true", "false"]:
        self.variables[name] = value.lower() == "true"
    elif self.is_number(value):
        self.variables[name] = self.convert_number(value)
    else:
        self.variables[name] = value
    self.save_config()
```

The priority order is: non-string passes through, then bool detection, then numeric detection, then raw string. This matters because YAML already types most values — the coercion path is only exercised when values arrive as strings from the CLI.

```python
def convert_number(self, value: str) -> int | float:
    if "." in value:
        return float(value)
    return int(value)
```

The dot-presence heuristic for int vs float is simple and correct for robot config values.

## Path Resolution

The robot stores maps, logs, and other artifacts relative to the config directory. `resolve_path` handles the ambiguity between absolute and relative paths:

```python
def resolve_path(self, path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path
    return (self.control_dir / path).resolve()
```

`ensure_subdirs` calls this to create the `maps/` and `logs/` directories on first use, so callers never have to check.

## Test Environment Detection

A subtle but important design: `detect_test_environment` sets `dry_run = True` when pytest or unittest is present in `sys.modules`. This propagates to `MovementApi.cmd_vel_helper`, which skips real hardware commands in tests without requiring explicit mocking of the hardware layer.

```python
def detect_test_environment(self):
    if "pytest" in sys.modules or "unittest" in sys.modules:
        self.variables["dry_run"] = True
```

## Launch Templates

The config file also carries launch templates — named command templates with default parameters. `ConfigManager` exposes these as a plain dict; `ProcessApi` consumes them to build `LaunchConfig` objects. The separation keeps `ConfigManager` free of any subprocess knowledge.

```python
def get_launch_templates(self) -> dict:
    return self.variables.get("launch_templates", {})
```

## Observations

- **No schema validation.** Missing required keys (e.g., `linear_speed`) surface as `None` from `get_variable`, caught only at point of use. A startup `validate()` would catch config errors earlier.
- **Save on every set.** `set_variable` calls `save_config()` unconditionally. A transactional API or explicit `flush()` would be more efficient for bulk updates.
- **Flat namespace.** All variables are top-level. Nested sections (hardware, nav, speech) would make the config file more readable but require deeper access helpers.
