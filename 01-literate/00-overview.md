---
version: "1.0"
generated: "2026-05-06"
---

# Control Package: Theory of Operation

## What This Is

`control` is a ROS2 package that gives a mobile robot a voice-driven command interface. A user speaks a command; the robot wakes, transcribes, maps intent, and executes motion or process actions — all over ROS2 topics and services. There is also a REST API and a CLI for scripted or remote control.

## Architecture in Layers

```
┌─────────────────────────────────────────────────────┐
│              Entry Points                           │
│   simple_cli.py   │   REST API   │  Voice Pipeline  │
└────────┬──────────┴──────┬───────┴────────┬─────────┘
         │                 │                │
         ▼                 ▼                ▼
┌─────────────────────────────────────────────────────┐
│           CommandDispatcher  /  IntentMapper        │
│      (parse text commands → structured objects)     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 RobotController                     │
│      (business logic, coordinates APIs, returns     │
│       uniform CommandResponse on every call)        │
└──┬─────────────┬──────────────┬────────────┬────────┘
   │             │              │            │
   ▼             ▼              ▼            ▼
MovementApi  CalibrationApi  ProcessApi  IntentApi
   │             │              │            │
   └─────────────┴──────────────┴────────────┘
                       │
                       ▼ (ROS2 topics / services)
                   Robot Hardware
```

## Voice Pipeline

```
Microphone
    │
    ▼
WakeWordDetector   ←── openwakeword model ("alexa")
    │ (wake detected)
    ▼
STTHelper          ←── Vosk GRPC or local model
    │ (transcript)
    ▼
IntentMapper       ←── maps phrase → IntentCommand
    │
    ▼
BehaviorManager    ←── selects behavior class
    │
    ▼
MotionBehavior / PerceptionBehavior / ...
    │
    ▼
ROS2 topics → robot execution
```

The voice pipeline runs inside `VoiceInputNode` (a ROS2 lifecycle node). `VoiceRuntime` encapsulates the non-ROS audio logic so it can be smoke-tested on a Pi without a running ROS graph.

## Configuration Foundation

Everything starts with `ConfigManager`. It loads a YAML file, coerces types, manages subdirectory creation, and detects test vs. production environments. Nearly every other module takes a `ConfigManager` instance at construction. Read `01-config_manager` first.

## Command Object Hierarchy

Commands are dataclasses organized in a hierarchy:

```
BaseCommand
├── MovementCommand  (drive, spin, stop)
├── LaunchCommand    (start/stop ROS launch files)
├── SystemCommand    (status, shutdown)
├── IntentCommand    (voice-originated, carries confidence)
└── SemanticCommand  (high-level: "go to kitchen")
```

`CommandDispatcher` parses text into these objects. `RobotController` executes them. The separation means new entry points (REST, voice, CLI) share the same execution path.

## Reading Order

| # | File | What it covers |
|---|------|----------------|
| 01 | config_manager | YAML config, factory pattern, type coercion |
| 02 | base_api | ROS2 node base class, shared plumbing |
| 03–06 | movement/intent/calibration/process_api | Four ROS2 API nodes |
| 07–10 | contracts and command dataclasses | Announcement contract, command type hierarchy |
| 11 | robot_controller | Business logic, lazy API init, uniform responses |
| 12 | command_dispatcher | Text → command object parsing |
| 14 | simple_cli | CLI entry point |
| 15 | intent_mapper | Phrase → IntentCommand mapping |
| 16–18 | wake_word, stt, voice_runtime | Audio pipeline components |
| 19–21 | ROS2 voice nodes | VoiceInputNode, SpeechOutputNode, BehaviorManagerNode |
| 22–24 | behaviors, intent_publisher | Motion/perception behaviors, intent publishing |

Appendices (X01–X09) cover parameter definitions, command schemas, and stub modules — useful for reference but not required for understanding the core architecture.

## Key Design Decisions

**Uniform return type.** Every `RobotController` method returns `CommandResponse(success, message, data)`. No exceptions escape to callers.

**Lazy node initialization.** ROS2 nodes are expensive. APIs are constructed on first use, not at startup. Status reporting checks for `None` directly.

**Separation of voice logic from ROS.** `VoiceRuntime` runs without ROS. `VoiceInputNode` wraps it. This lets audio tuning happen on a Pi without a full ROS graph.

**Intent over raw commands.** Voice input goes through `IntentMapper` → `IntentCommand` rather than directly to movement commands. This decouples the speech vocabulary from the robot action set.
