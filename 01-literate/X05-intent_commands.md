---
version: "1.0"
generated: "2026-05-04"
---

# Intent Commands (Appendix)

`intent_commands.py` defines CLI commands that publish to the `/intent` topic.

```python
"intent.stop":          CommandDef("publish_intent_stop",           [], ...)
"intent.explore":       CommandDef("publish_intent_explore",        [], ...)
"intent.describe_scene":CommandDef("publish_intent_describe_scene", [], ...)
"intent.count_objects": CommandDef("publish_intent_count_objects",
                            [ParameterDef("object_type", str, True, ...)], ...)
```

These are the raw intent publishing commands. `scene.describe` and `scene.count` in `semantic_commands.py` map to the same `RobotController` methods with more user-friendly names. The `intent.*` variants are kept for completeness and debugging.
