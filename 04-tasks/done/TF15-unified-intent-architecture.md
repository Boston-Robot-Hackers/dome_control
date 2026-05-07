# Tasks for Feature F15

## Testing Tiers

Each task should be verified at the highest tier available before moving on:

- **No-ROS** — pure Python, `pytest` only, no `rclpy`. Fastest, runs anywhere.
- **ROS2 no-robot** — needs ROS2 running, no physical hardware. Dev machine or Pi without motors active.
- **Hardware** — physical robot required.

Prefer no-ROS tests. Use mock/stub ROS nodes for ROS2 tests.

## T01 — Rename BehaviorManager to IntentParser
**Status**: done
**Test tier**: No-ROS
**Description**: Rename class `BehaviorManager` → `IntentParser` in
`behavior_manager.py`. Update all imports and references. No logic changes.

**Test**: `python3 -m pytest test/test_behavior_manager.py -v` — 6 passed.

---

## T02 — Create behaviors package with MotionBehavior
**Status**: done
**Test tier**: No-ROS (mock RobotController)
**Description**: Created `control/behaviors/__init__.py`,
`control/behaviors/motion_behavior.py`, stub `perception_behavior.py`.
`MotionBehavior` with `handles()` and `execute(intent, node)`. Wired to
`RobotController`: `stop` → `stop_robot()`, `drive_square` → `script_square(meters)`,
`explore` → no-op (not yet implemented).

**Test**: `python3 -m pytest test/test_motion_behavior.py -v` — 10 passed.

---

## T03 — Create PerceptionBehavior
**Status**: done
**Test tier**: No-ROS (mock node + fake std_srvs module injected via sys.modules)
**Description**: Implemented `control/behaviors/perception_behavior.py`. Moved
`call_describe_scene`, `on_describe_scene_done`, `publish_announcement` logic
from `behavior_manager_node.py` into `PerceptionBehavior`. Uses lazy import for
`std_srvs.srv.Trigger` to avoid rclpy at module load. Handles `describe_scene`
and `count_objects` (count_objects logs unimplemented).

**Test**: `python3 -m pytest test/test_perception_behavior.py -v` — 11 passed.

---

## T04 — Refactor BehaviorManagerNode to use both handlers
**Status**: done
**Test tier**: No-ROS (fake rclpy + geometry_msgs + nav_msgs injected via sys.modules)
**Description**: Refactor `behavior_manager_node.py`:
- Instantiate `RobotController(ConfigManager())` and both behavior handlers
- Replace inline dispatch with handler loop:
  ```python
  for handler in self.handlers:
      if handler.handles(intent.name):
          handler.execute(intent, self)
          return
  self.get_logger().warn(f"Unhandled intent: {intent.name}")
  ```
- Remove inline `call_describe_scene` / `on_describe_scene_done` (now in PerceptionBehavior)
- Remove `describe_scene_client` setup from node `__init__` (now owned by PerceptionBehavior)
- Keep `IntentParser.parse_intent()` call

**Test**: `python3 -m pytest test/test_behavior_manager_node_routing.py -v` — 5 passed.

---

## T05 — Absorb simple_parser into CommandDispatcher
**Status**: done
**Test tier**: No-ROS
**Description**: Add `CommandDispatcher.dispatch_text(text: str) ->
CommandResponse`: tokenize input, extract command name and params, call
`execute()`. Delete `control/interface/simple_parser.py`. Update `simple_cli.py`
to call `dispatcher.dispatch_text()`.

**Test**: `python3 -m pytest test/test_command_dispatcher_text.py -v` — 14 passed.
Bonus: `conftest.py` created with shared fake ROS2 injection; fixed 111 previously-failing tests.
Full suite: 158/173 passed; 15 failures all pre-existing config path issues.

---

## T06 — CLI behavior commands publish to /intent
**Status**: done
**Test tier**: ROS2 no-robot (IntentPublisher wraps an rclpy publisher; inject
mock publisher in tests to keep unit tests No-ROS, but integration requires ROS2)
**Description**: In `CommandDispatcher`, behavior commands route to `/intent`
instead of calling `RobotController` directly. Add thin `IntentPublisher` helper
that `CommandDispatcher` uses to publish. Design `IntentPublisher` to accept an
injected publish callable so unit tests stay No-ROS.

Behavior command → intent name mapping:
- `stop` → `stop`
- `explore` → `explore`
- `scene.describe` / `scene describe` → `describe_scene`
- `scene.count` / `scene count` → `count_objects`
- `drive_square` → `drive_square`

All return `CommandResponse(True, "Intent published: <name>")` immediately.

**Test**: Extend `test_command_dispatcher_text.py` (No-ROS with mock publisher):
- `dispatch_text("stop")` publishes correct intent JSON
- `dispatch_text("scene describe")` publishes `describe_scene` intent
- `dispatch_text("move forward 1.0")` does NOT publish intent (direct path)

**Test**: `python3 -m pytest test/test_command_dispatcher_text.py -v` — 19 passed.
Full suite: 164/179 passed; 15 failures all pre-existing.

---

## T07 — Remove intent and semantic commands from registry
**Status**: done
**Test tier**: No-ROS
**Description**: Remove `intent_cmd.build_intent_commands()` and
`sem_cmd.build_semantic_commands()` from `CommandDispatcher._build_command_registry()`.
Delete or archive `intent_commands.py` and `semantic_commands.py` — replaced by
T06 routing logic.

**Test**: 156/171 passed; 15 pre-existing failures (config path). 8 net tests removed
(11 old registry tests → 5 new dispatch_text tests). No regressions.

---

## T08 — Smoke test end-to-end
**Status**: done
**Test tier**: ROS2 no-robot (all steps — verify topic publishes, not robot movement)
**Description**: Manual verification with ROS2 running:
1. CLI `stop` → `/intent` topic receives stop intent, behavior_manager handles it
2. CLI `scene describe` → `/announcement` published
3. `ros2 topic pub /intent std_msgs/String '{"name":"stop","source":"test","slots":{}}'`
   → same result as step 1
4. CLI `move forward 1.0` → `/cmd_vel` topic receives twist message (verify with `ros2 topic echo`)
5. CLI `map list` → synchronous response in REPL
6. CLI `config list` → synchronous response in REPL

Run: `python3 -m pytest test/ -v`

**Test**: ROS2 no-robot smoke test completed manually.
