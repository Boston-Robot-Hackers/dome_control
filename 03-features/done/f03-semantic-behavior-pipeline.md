# Feature description for feature F03
## F03 — Semantic behavior pipeline MVP
**Priority**: High
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Add the first end-to-end semantic command path on top of the
existing intent publisher. The CLI should expose user-facing commands such as
`scene.describe` and `scene.count` that publish normalized `/intent` JSON. A
minimal behavior manager should subscribe to `/intent`, handle `describe_scene`
by calling a describe-scene service, and publish or log the resulting summary.
This keeps voice, REST, and button input deferred while proving the shared
intent-to-behavior contract.

## How to Demo
**Setup**: ROS2 environment sourced. `oak_roboflow_ros` may be running for live
target data later; the current demo uses the included stub describe-scene service.

**Steps**:
1. Terminal 1: run the behavior manager node.
2. Terminal 2: run a describe-scene service provider.
3. Terminal 3: `ros2 run control run`
4. In REPL: type `scene describe`
5. Optional: type `scene count can`

**Expected output**: the CLI publishes a `/intent` JSON message, the behavior
manager receives it, calls the query service, and reports a summary such as
`I see 2 cups and 1 can`.
