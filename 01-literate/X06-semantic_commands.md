---
version: "1.0"
generated: "2026-05-04"
---

# Semantic Commands (Appendix)

`semantic_commands.py` defines user-friendly aliases for the two most common intent commands.

```python
"scene.describe": CommandDef("publish_intent_describe_scene", [], ...)
"scene.count":    CommandDef("publish_intent_count_objects",
                     [ParameterDef("object_type", str, True, ...)], ...)
```

These map to the same `RobotController` methods as `intent.describe_scene` and `intent.count_objects`. The `scene.*` vocabulary is preferred for interactive use ("scene describe" reads more naturally than "intent describe_scene"). The `intent.*` forms remain available for scripting and debugging.
