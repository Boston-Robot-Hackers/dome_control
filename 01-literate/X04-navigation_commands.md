---
version: "1.1"
generated: "2026-06-24"
---

# Navigation Commands

`navigation_commands.py` is the command registry for all map management and navigation
operations in dome_control. It returns a flat dictionary of `CommandDef` entries keyed by
dotted names like `"map.save"` or `"nav.go"`. The calling infrastructure in
`CommandDispatcher` uses these keys to route CLI input to the right method on
`RobotController`.

The file imports two thin descriptor types rather than any ROS2 machinery:

```python
import dome_control.commands.command_def as cd
import dome_control.commands.parameter_def as pd
```

This is deliberate: command *definitions* are pure data. No nodes, no publishers, no
subscriptions live here. The ROS2 plumbing lives in `RobotController`; this file just
describes the surface area.

---

## Map group

Three commands handle persistence of the SLAM map. All three are parameterless because the
map name is read from the `map_name` config variable at execution time, not typed on the
command line. This avoids the error-prone pattern of re-typing a filename and ensures the
same name is used consistently across save and serialize operations.

```python
"map.save": cd.CommandDef(
    method_name="map_save",
    parameters=[],
    description="Save current map to maps/ folder (uses map_name variable)",
    group="map"
),
"map.list": cd.CommandDef(
    method_name="list_maps",
    parameters=[],
    description="List available maps in maps/ folder",
    group="map"
),
"map.serialize": cd.CommandDef(
    method_name="map_serialize",
    parameters=[],
    description="Save current map in SLAM Toolbox serialized format (uses map_name variable)",
    group="map"
),
```

`map.save` drives `nav2_map_server map_saver_cli`, producing the standard `.pgm`/`.yaml`
pair. `map.serialize` calls the SLAM Toolbox `SerializePoseGraph` service, which saves the
full graph (not just the occupancy grid) so that localization can resume exactly where it
left off. Both are synchronous shell-out operations wrapped in `ProcessApi.run_command_sync`
inside `RobotController`.

`map.list` is a read-only convenience command that scans the `maps/` folder and prints
available files. It requires no ROS2 interaction at all.

---

## Nav group

The navigation commands translate high-level user intent into ROS2 action or topic
interactions. They are split along a clear axis: commands that *cause* something to happen
publish an intent topic; the one command that *reads* something queries a status topic
instead.

### nav.go — navigate to a labeled object

```python
"nav.go": cd.CommandDef(
    method_name="publish_intent_navigation_go",
    parameters=[pd.ParameterDef("label", str, True, None, "Object label to navigate to")],
    description="Navigate to nearest confirmed object with given label",
    group="nav"
),
```

`nav.go` is the only command in this file that takes a required parameter. The `label`
argument names the semantic object type (e.g. `"chair"`, `"door"`) that the robot should
navigate toward. The `RobotController` method `publish_intent_navigation_go` publishes on
the intent bus; a downstream node resolves the label to a pose by consulting the object
detection history and then sends a Nav2 `NavigateToPose` goal.

Requiring `label` as a positional CLI argument rather than a config variable is the right
tradeoff here: navigation targets change frequently during a session whereas the map name
does not.

### nav.cancel — abort current navigation

```python
"nav.cancel": cd.CommandDef(
    method_name="publish_intent_navigation_cancel",
    parameters=[],
    description="Cancel current navigation goal",
    group="nav"
),
```

A parameterless escape hatch. `publish_intent_navigation_cancel` publishes on the intent
topic; the navigation node cancels any active `NavigateToPose` or `FollowWaypoints` goal
on receipt. Keeping cancel as a separate command (rather than passing a flag to `nav.go`)
makes it keyboard-friendly and allows the CLI to bind it to a single keystroke.

### nav.explore — start frontier exploration

```python
"nav.explore": cd.CommandDef(
    method_name="publish_intent_exploration_start",
    parameters=[],
    description="Start autonomous frontier exploration",
    group="nav"
),
```

Triggers the `explore_lite` (or equivalent) frontier exploration pipeline. Publishing an
intent rather than calling the action server directly keeps the command layer decoupled from
the specific exploration library in use — the intent subscriber owns that binding.

### nav.explore.stop — halt frontier exploration

```python
"nav.explore.stop": cd.CommandDef(
    method_name="publish_intent_exploration_stop",
    parameters=[],
    description="Stop autonomous frontier exploration",
    group="nav"
),
```

The counterpart to `nav.explore`. Publishes an intent that signals the exploration node to
cancel its active frontier goal and return to idle. This is kept separate from `nav.cancel`
because exploration and point-to-point navigation can coexist in the system model; each has
its own cancel path.

### nav.explore.status — read exploration state

```python
"nav.explore.status": cd.CommandDef(
    method_name="explore_status",
    parameters=[],
    description="Read current /explore/status topic value",
    group="nav"
),
```

This command is intentionally different in character from every other command in this file.
All other nav commands *publish* an intent; `nav.explore.status` *reads* a topic. The
method name `explore_status` (no `publish_intent_` prefix) signals that distinction
explicitly.

The rationale: exploration is a long-running background process. The operator needs
observable feedback — is it still running, did it complete, did it fail? Polling
`/explore/status` gives a synchronous snapshot of the exploration node's reported state
without requiring a separate monitoring terminal. The implementation in `RobotController`
subscribes to `/explore/status` with a short timeout and returns the most recent message
value to the CLI.
