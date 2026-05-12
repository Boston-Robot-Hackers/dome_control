---
version: "1.1"
generated: "2026-05-12"
---

# dome_control Package: Theory of Operation

## What This Is

`dome_control` is a ROS2 package that gives a mobile robot a voice-driven command interface. A user speaks a command; a sibling package (`robot_voice`) transcribes and maps the intent, then publishes it to `/intent`. This package receives that intent, routes it to a domain behavior handler, and executes motion or perception actions — all over ROS2 topics and services. There is also a CLI for scripted or remote control.

## Architecture in Layers

```
┌─────────────────────────────────────────────────────┐
│              Entry Points                           │
│         simple_cli.py   │   /intent topic           │
└────────┬────────────────┴─────────────┬─────────────┘
         │                              │
         ▼                              ▼
┌────────────────────┐     ┌────────────────────────────┐
│  CommandDispatcher │     │    BehaviorManagerNode     │
│  (text → command)  │     │  (intent → handler)        │
└────────┬───────────┘     └──────┬──────────┬──────────┘
         │                        │          │
         ▼                        ▼          ▼
┌────────────────┐    ┌──────────────┐  ┌───────────────────┐
│ RobotController│    │MotionBehavior│  │PerceptionBehavior │
│ (business logic│    │(movement via │  │(describe_scene /  │
│  uniform resp) │    │ RobotCtrl)   │  │ list_objects)     │
└──┬──────┬──────┘    └──────────────┘  └───────────────────┘
   │      │
   ▼      ▼
MovementApi  ProcessApi  CalibrationApi  IntentApi
   │
   ▼  (ROS2 topics / services)
Robot Hardware
```

## Intent Flow

Voice input lives in the sibling package `robot_voice`. Its pipeline produces JSON intent strings on `/intent`. This package consumes them:

```
robot_voice package
    VoiceInputNode
        │ (JSON intent string)
        ▼
    /intent topic
        │
        ▼
dome_control package
    BehaviorManagerNode
        │
        ├── MotionBehavior   (stop, explore, drive, turn, status)
        └── PerceptionBehavior  (describe_scene, list_objects)
                │
                ▼
        /announcement topic
                │
                ▼
        SpeechOutputNode  (text → Piper TTS → speaker)
```

## Two Execution Paths

`CommandDispatcher` routes to one of two paths:

**Behavior path**: Commands that involve intent semantics (`scene describe`, `scene objects`, intent verbs) publish JSON to `/intent` via `IntentPublisher`. Query intents wait up to 5s for a reply on `/announcement`.

**Direct path**: All other commands (`move`, `launch`, `status`, `calibrate`) call `RobotController` methods synchronously and return a `CommandResponse`.

## Configuration Foundation

Everything starts with `ConfigManager`. It loads a YAML file, coerces types, manages subdirectory creation, and detects test vs. production environments. Nearly every other module takes a `ConfigManager` instance at construction. Read `01-config_manager` first.

## Vision Integration

`BehaviorManagerNode` optionally loads class profiles from `dome_vision` at startup:

```python
self.declare_parameter("class_profiles_path", DEFAULT_VISION_CONFIG)
# loads self.profiles and self.label_map
```

`PerceptionBehavior` uses these to map raw vision model class IDs to human-readable display names. If `dome_vision` is absent, the node starts normally and falls back to raw class IDs.

## Command Object Hierarchy

Commands are dataclasses organized in a hierarchy:

```
BaseCommand
├── MovementCommand    (drive, spin, stop)
├── LaunchCommand      (start/stop ROS launch files)
├── SystemCommand      (status, shutdown)
├── NavigationCommand  (map operations)
└── IntentCommand      (behavior path commands)
```

`CommandDispatcher` parses text into these objects. `RobotController` executes them. New entry points share the same execution path.

## Launch Structure

Each package owns its own launch files:

| Package | Launch | What it starts |
|---------|--------|----------------|
| `dome_control` | `robot.launch.py` | `speech_output`, `behavior_manager` |
| `dome_control` | `remote.launch.py` | optional `behavior_manager` |
| `robot_voice` | `robot.launch.py` | `voice_input` |
| `oak_roboflow_ros` | `robot.launch.py` | oak camera, semantic_map |

## Reading Order

| # | File | What it covers |
|---|------|----------------|
| 01 | config_manager | YAML config, factory pattern, type coercion |
| 02 | base_api | ROS2 node base class, shared plumbing |
| 03–06 | movement/intent/calibration/process_api | Four ROS2 API nodes |
| 07 | announcement_contract | Shared message contract for /announcement |
| 08–10 | movement/launch/system_commands | Command dataclasses by domain |
| 11 | robot_controller | Business logic, lazy API init, uniform responses |
| 12 | command_dispatcher | Text → command object parsing |
| 13 | speech_api | CLI-side announcement publisher |
| 14 | simple_cli | CLI entry point, REPL and non-interactive modes |
| 18 | behavior_manager (IntentParser) | Pure JSON→Intent parsing |
| 19 | behavior_manager_node | ROS2 intent router, vision profile loading |
| 20 | voice_input_node | (orphaned — source moved to robot_voice) |
| 21 | speech_output_node | Piper TTS, /announcement consumer |
| 22 | motion_behavior | Motion intent execution via RobotController |
| 23 | perception_behavior | describe_scene service call, list_objects from cache |
| 24 | intent_publisher | JSON intent publishing with query reply wait |

Appendices (X01–X09) cover parameter definitions, command schemas, and stub modules.

## Key Design Decisions

**Uniform return type.** Every `RobotController` method returns `CommandResponse(success, message, data)`. No exceptions escape to callers.

**Lazy node initialization.** ROS2 nodes are expensive. APIs are constructed on first use, not at startup.

**Intent over raw commands.** Voice input goes through `IntentParser` → `IntentCommand` → `BehaviorManagerNode` rather than directly to movement commands. Decouples speech vocabulary from robot action set.

**Unconditional service call.** `PerceptionBehavior.call_describe_scene` calls `/describe_scene` even when `service_is_ready()` is `False`, to handle transient startup delays. Future silently stalls if service never appears.

**Vision degradation.** Both `dome_vision` import and label map loading are wrapped in `try/except`. System runs without vision; perception responses degrade to raw class IDs, not crashes.
