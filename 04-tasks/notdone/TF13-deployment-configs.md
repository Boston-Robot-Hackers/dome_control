# Tasks for Feature F13

## T01 — Create launch/onboard.launch.py
**Status**: not done
**Description**: Write `launch/onboard.launch.py`. Always starts `speech_output`
and `describe_scene_stub`. Launch args: `voice:=false` (adds `voice_input_node`
when true), `behavior:=true` (adds `behavior_manager` when true). Pass relevant
env vars through to each node.

## T02 — Create launch/offboard.launch.py
**Status**: not done
**Description**: Write `launch/offboard.launch.py`. Launch args: `voice:=true`
(adds `voice_input_node`), `behavior:=false` (adds `behavior_manager`). Pass
relevant env vars through. No nodes are unconditional — file may start nothing
if both args are false.

## T03 — Update CMakeLists.txt to install launch/
**Status**: not done
**Description**: Add `install(DIRECTORY launch/ DESTINATION share/${PROJECT_NAME})`
to `CMakeLists.txt` so launch files are installed and discoverable by
`ros2 launch control`.

## T04 — Smoke test config A (everything onboard)
**Status**: not done
**Description**: On robot, run `ros2 launch control onboard.launch.py voice:=true`.
Confirm all four nodes start: `speech_output`, `describe_scene_stub`,
`behavior_manager`, `voice_input`. Say wake word, confirm intent flows end to end.

## T05 — Smoke test config B (mic offboard)
**Status**: not done
**Description**: Robot runs `ros2 launch control onboard.launch.py`. Offboard
machine runs `ros2 launch control offboard.launch.py`. Say wake word into offboard
mic. Confirm intent published offboard, speech plays on robot speaker.

## T06 — Smoke test config D (CLI offboard)
**Status**: not done
**Description**: Robot runs `ros2 launch control onboard.launch.py`. Offboard
machine runs `ros2 run control run`. Issue a CLI command. Confirm intent reaches
robot and behavior_manager responds.
