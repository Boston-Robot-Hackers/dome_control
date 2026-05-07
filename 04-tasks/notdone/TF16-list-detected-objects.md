# TF16 — List Detected Objects

## T01 — Subscribe to /oak/detections in behavior_manager_node
**Status**: not done
**Description**: Add a subscription to `/oak/detections` (Detection2DArray) in
`behavior_manager_node.py`. Cache the latest message in `self.latest_detections`.
Initialize to `None`. No test needed — ROS subscriber wiring.

## T02 — Implement list_objects in PerceptionBehavior
**Status**: not done
**Description**: Add `list_objects` to `PERCEPTION_INTENTS`. In `execute()`, read
`self.node.latest_detections`, format labels+scores into a string, call
`publish_announcement()`. If `None` or empty, announce "No objects detected."
Write unit test with mock detections.

## T03 — Add CLI command
**Status**: not done
**Description**: Add `scene objects` (or `objects`) to the CLI dispatcher in control.
Direct path — calls `RobotController` method that reads latest detections via a
ROS topic subscription or service. Announce result. Write unit test.

## T04 — Add voice command to robot_voice
**Status**: not done
**Description**: In `robot_voice/intent_mapper.py` add `(("objects",), "list_objects")` to
`PHRASE_INTENTS`. In `runtime.py` add `"objects"` to `DEFAULT_GRAMMAR` and
`TUNED_VOICE_PARAMETERS["stream_settings"]["grammar"]`.

## T05 — Update robot.launch.py oak dependency
**Status**: not done
**Description**: Add `<depend>oak_roboflow_ros</depend>` to `control/package.xml`
so colcon resolves build order correctly when `oak:=true`.
