---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X13 — describe_scene stub node

`nodes/describe_scene_stub_node.py` serves `/describe_scene` and always
answers `"I see 2 cups and 1 can"`. It lets the voice → intent →
behavior_manager → announcement loop be smoke-tested without an OAK
camera or `dome_semantic`:

```bash
bl dome_control robot.launch.py
ros2 run dome_control describe_scene_stub
```

## Observations

- **It conflicts with the real server.** If `semantic_map` is also
  running, two servers share `/describe_scene` and either may answer. Its
  docstring should warn about that, or it could refuse to start when the
  service already exists.
- **It's labelled "temporary" but is still installed.** If it stays, make
  it a documented test fixture. If not, remove it from `CMakeLists.txt`
  and `scripts/`.
