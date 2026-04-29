# Tasks for Feature F03 — Semantic Behavior Pipeline MVP

## T01 — Add semantic command aliases
**Status**: done
**Description**: Add a `scene` command group that reuses `RobotController.publish_intent`.
Initial commands: `scene.describe` -> `describe_scene`, and `scene.count object_type=<label>`
-> `count_objects`. Keep the existing generic `intent.*` commands working.

## T02 — Register semantic commands
**Status**: done
**Description**: Register the semantic command module in `CommandDispatcher` and add help/docs
entries so users can discover `scene describe` and `scene count`.

## T03 — Implement behavior manager MVP
**Status**: done
**Description**: Add a minimal `behavior_manager_node` in this repo or a clearly documented
temporary module. It subscribes to `/intent` (`std_msgs/String` JSON), validates/parses
the intent, handles `describe_scene`, and logs unsupported intents without crashing.

## T04 — Add describe-scene service client path
**Status**: done
**Description**: For `describe_scene`, call a service that returns a human-readable scene
summary. If the final service definition is not ready, use the current temporary JSON/String
contract and document the migration path to custom `.srv` files.

## T05 — Add announcement output path
**Status**: done
**Description**: Publish the behavior manager response to an announcement topic or log it
through a single helper so it can later be replaced by `speech_output_node` without changing
intent handling logic.

## T06 — Tests for command publishing and behavior dispatch
**Status**: done
**Description**: Add tests for semantic command registration, published intent names/slots,
behavior manager JSON parsing, unsupported-intent handling, and describe-scene dispatch using
mocks rather than live ROS2 services where practical.

## T07 — Demo docs and handoff update
**Status**: done
**Description**: Document the three-terminal smoke test and update `02-doc/current.md` with
the feature number, current status, and next recommended step.
