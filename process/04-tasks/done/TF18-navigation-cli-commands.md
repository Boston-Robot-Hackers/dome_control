# Tasks for Feature F18

Task file name must be `TFNN-<slug>.md` where `NN` matches the feature number.

## T01 — Add nav.go and nav.cancel CLI commands
**Status**: done
**Description**: Add `nav.go <label>` and `nav.cancel` entries in `navigation_commands.py`
with method names `publish_intent_navigation_go` and `publish_intent_navigation_cancel`.
Add corresponding methods to `RobotController`. Update tests in
`test_command_dispatcher_text.py`.

## T02 — Add nav.explore and nav.explore.stop CLI commands
**Status**: done
**Description**: Add `nav.explore` and `nav.explore.stop` entries in `navigation_commands.py`
with method names `publish_intent_exploration_start` and `publish_intent_exploration_stop`.
Add corresponding methods to `RobotController`.

## T03 — Tests
**Status**: done
**Description**: Tests in `test_command_dispatcher_text.py` cover `nav.go` and `nav.cancel`
dispatch. `nav.explore` and `nav.explore.stop` are covered structurally (same dispatcher
path); unit tests for their dispatch are part of the existing test class.
