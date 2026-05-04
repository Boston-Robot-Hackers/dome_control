---
version: "1.0"
generated: "2026-05-04"
---

# Navigation Commands (Appendix)

`navigation_commands.py` defines three map management commands.

```python
"map.save":      CommandDef("map_save",      [], "Save current map to maps/ folder", group="map")
"map.list":      CommandDef("list_maps",     [], "List available maps in maps/ folder", group="map")
"map.serialize": CommandDef("map_serialize", [], "Save current map in SLAM Toolbox serialized format", group="map")
```

All three are parameterless — they read `map_name` from the config variable rather than from a CLI argument. `map.save` calls `nav2_map_server map_saver_cli`; `map.serialize` calls the SLAM Toolbox serialize service. Both are implemented in `RobotController` using `ProcessApi.run_command_sync`.
