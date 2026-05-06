# Feature description for feature F15
## F15 — Unified intent architecture with split behavior handlers
**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Refactor the command and behavior layers so that high-level
behaviors are triggerable from any source — CLI, `/intent` topic, speech, future
REST API — through a single consistent path. Primitives and admin commands keep
their direct synchronous CLI path. Split `BehaviorManager` into domain-specific
handlers. Reduce unnecessary layers.

## Background

Current architecture has two disconnected paths:

1. **CLI path**: `simple_cli` → `simple_parser` → `CommandDispatcher` →
   `RobotController` → `Ros2Api`
2. **Intent path**: any source → `/intent` topic → `BehaviorManagerNode` →
   `BehaviorManager` (parses only, no execution) → dead end for most intents

Problems:
- `BehaviorManager` can parse intents but cannot execute them (no access to
  `RobotController` or `Ros2Api`)
- `intent.stop` publishes correctly but `behavior_manager` does nothing with it
- Speech, topic publish, and future API have no way to trigger behaviors or scripts
- Adding a new behavior requires changes in both CLI command files and the
  behavior manager separately
- `simple_parser` is a separate layer from `CommandDispatcher` with overlapping
  responsibility

## Target Architecture

Two paths, clearly owned:

### Path A — Behaviors (intent-driven)
All high-level behaviors go through `/intent`. Any source triggers them
identically.

```
CLI (behavior cmd)  ──┐
Speech               ──┤  publish JSON to /intent topic
Topic publish        ──┤
Future REST API      ──┘
                          │
                          ▼
                  BehaviorManagerNode   (ROS node, router)
                          │  IntentParser.parse_intent()
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
       MotionBehavior         PerceptionBehavior
       (stop, explore,        (describe_scene,
        drive_square)          count_objects)
               │                     │
               └──────┬──────────────┘
                      ▼
               RobotController   (execution core, unchanged)
                      │
                   Ros2Api
                      │
               ROS topics/services
```

Behaviors: `stop`, `explore`, `drive_square`, `describe_scene`, `count_objects`

### Path B — Direct (CLI only, synchronous)
Primitives and admin commands bypass intent. CLI stays synchronous with real
responses.

```
CLI (primitive/admin cmd)
        │
        ▼
CommandDispatcher  (parameter validation, routing)
        │
        ▼
RobotController
        │
     Ros2Api
```

Direct commands: all `move.*`, `turn.*`, `map.*`, `launch.*`, `config.*`,
`system.*`, `robot.status`

**Policy:** primitives and admin are CLI-direct only. When a specific primitive
is needed via speech or topic, add a dedicated intent for it at that time. Do
not pre-emptively add intent versions of primitives.

## Layer Reduction

Current path A (CLI intent): 8 layers → target: 6 (CLI publishes directly,
no `CommandDispatcher` hop for behaviors)

Current path B (CLI direct): 5 layers → target: 4 (`simple_parser` merged
into `CommandDispatcher.dispatch_text()`)

## New Files

```
control/behaviors/__init__.py
control/behaviors/motion_behavior.py       # MotionBehavior
control/behaviors/perception_behavior.py   # PerceptionBehavior
control/commands/intent_publisher.py       # IntentPublisher (injectable for tests)
control/nodes/__init__.py
```

## Modified Files

- `control/commands/intent_parser.py` — renamed from `behavior_manager.py`;
  class `BehaviorManager` → `IntentParser`; file moved to `commands/`
- `control/nodes/behavior_manager_node.py` — moved from root; added
  `RobotController`, routes to handler list, removed inline `describe_scene` logic
- `control/commands/command_dispatcher.py` — absorbed text-parsing from
  `simple_parser`; behavior commands publish to `/intent` via `IntentPublisher`;
  behavior commands added to registry so they appear in `help commands`
- `control/interface/simple_cli.py` — calls `dispatcher.dispatch_text()` directly

## Deleted Files

- `control/interface/simple_parser.py` — logic merged into `CommandDispatcher`
- `control/commands/intent_commands.py` — replaced by `BEHAVIOR_COMMANDS` routing
- `control/commands/semantic_commands.py` — replaced by `BEHAVIOR_COMMANDS` routing

## Behavior Handler Interface

Each handler implements:

```python
def handles(self, intent_name: str) -> bool: ...
def execute(self, intent: Intent, node: Node) -> None: ...
```

`node` passed to `execute` for handlers needing async ROS calls
(PerceptionBehavior). MotionBehavior ignores it.

## MotionBehavior

Intents: `stop`, `explore`, `drive_square`

Holds reference to `RobotController`. Calls are synchronous/blocking — run in
executor thread to avoid blocking the ROS spin.

## PerceptionBehavior

Intents: `describe_scene`, `count_objects`

Holds reference to the ROS node for service clients. Calls are async via future
callbacks. Publishes to `/announcement` on completion.

## IntentParser (renamed from BehaviorManager)

Unchanged responsibility: parse raw JSON string → `Intent(name, source, slots)`.
No execution. No ROS imports.

## RobotController

Unchanged. Both behavior handlers and CLI direct path call into it. No awareness
of intent routing.

## CLI Behavior Command Flow

When user types `scene describe` or `stop`:

1. `CommandDispatcher` recognizes it as a behavior command
2. Publishes `{"name": "describe_scene", "source": "cli", "slots": {}}` to
   `/intent` via a thin publisher helper
3. Returns `CommandResponse(True, "Intent published: describe_scene")`

CLI gets immediate acknowledgement. Execution result arrives via `/announcement`.

## Extensibility

Adding a new behavior:
1. Add intent name to `MotionBehavior.handles()` or `PerceptionBehavior.handles()`
2. Add `elif` branch in `execute()`
3. Add handler method to `RobotController` if needed

Adding a new behavior domain:
1. Create `control/behaviors/<domain>_behavior.py`
2. Append to `self.handlers` in `BehaviorManagerNode.__init__()`

Promoting a primitive to intent-driven (when speech needs e.g. `move_forward`):
1. Add intent to `MotionBehavior`
2. Add CLI alias that publishes the intent (direct CLI command can coexist)
3. Add phrase to voice grammar in `voice/runtime.py`
Do this only when a concrete use case requires it.

## Future Intent Candidates (not in scope, for reference)

- `rotate_stress`, `circle_stress` — already have `RobotController` methods
- `start_navigation`, `stop_navigation` — voice-friendly launch control
- `report_status` — speak robot state via `/announcement`
- `save_map` — "save map" as voice command
- `go_home`, `patrol`, `find_object <type>`, `navigate_to <location>`, `follow`
- `announce <text>` — publish arbitrary text to `/announcement`

## Tests

Existing tests that should keep passing unchanged:
- `test_behavior_manager.py` — `IntentParser` rename is mechanical; same logic
- `test_announcement_contract.py` — no change to contract
- `RobotController` method tests — execution layer unchanged

New tests required:
- `test_motion_behavior.py` — `handles()` correct; `execute()` calls correct
  `RobotController` method per intent; unknown intent ignored
- `test_perception_behavior.py` — `handles()` correct; `execute()` triggers
  service call; failed service logs warning
- `test_command_dispatcher_text.py` — absorbed text parsing produces correct
  command name and params; behavior commands return intent-published response
- `test_behavior_manager_node_routing.py` — routes known intents to correct
  handler; unknown intent logs warning

## How to Demo

**Setup**: ROS2 running, `behavior_manager` node started.

**Steps**:
1. CLI: `scene describe` → publishes intent → behavior_manager → `/announcement`
2. CLI: `stop` → publishes intent → `MotionBehavior` calls `stop_robot()`
3. Shell: `ros2 topic pub /intent std_msgs/String '{"name":"stop","source":"test","slots":{}}'`
   → same result as step 2
4. CLI: `move forward 1.0` → direct path, synchronous response
5. CLI: `map list` → direct path, synchronous response

**Expected output**: steps 1–3 identical regardless of source; steps 4–5 return
synchronous REPL responses.
