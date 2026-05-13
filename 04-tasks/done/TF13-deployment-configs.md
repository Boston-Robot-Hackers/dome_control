# Tasks for Feature F13

## T01 — Update launch/robot.launch.py
**Status**: done
**Description**: Write `launch/robot.launch.py`. Always starts `speech_output`
and `describe_scene_stub`. Launch args: `--voice False` (adds `voice_input_node`
when true), `--behavior True` (adds `behavior_manager` when true). Pass relevant
env vars through to each node.
Use `better_launch` for the launch file.

## T02 — Update launch/remote.launch.py
**Status**: done
**Description**: Write `launch/remote.launch.py`. Launch args: `--voice True`
(adds `voice_input_node`), `--behavior False` (adds `behavior_manager`). Pass
relevant env vars through. No nodes are unconditional — file may start nothing
if both args are false.
Use `better_launch` for the launch file.

## T03 — Update CMakeLists.txt to install launch/
**Status**: done
**Description**: Add `install(DIRECTORY launch/ DESTINATION share/${PROJECT_NAME})`
to `CMakeLists.txt` so launch files are installed and discoverable by
`bl dome_control <launch-file>`.

## T04 — Smoke test config A (everything onboard)
**Status**: done
**Description**: On robot, run `bl dome_control robot.launch.py --voice True`.
Confirm all four nodes start: `speech_output`, `describe_scene_stub`,
`behavior_manager`, `voice_input`. Say wake word, confirm intent flows end to end.

## T05 — Smoke test config B (mic offboard)
**Status**: done
**Description**: Robot runs `bl dome_control robot.launch.py`. Offboard
machine runs `bl dome_control remote.launch.py`. Say wake word into offboard
mic. Confirm intent published offboard, speech plays on robot speaker.

## T06 — Smoke test config D (CLI offboard)
**Status**: done
**Description**: Robot runs `bl dome_control robot.launch.py`. Offboard
machine runs `ros2 run dome_control run`. Issue a CLI command. Confirm intent reaches
robot and behavior_manager responds.
