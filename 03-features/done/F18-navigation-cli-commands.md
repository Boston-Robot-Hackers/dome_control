# Feature description for feature F18
Feature file name must be `FNN-<slug>.md` where `NN` matches the feature number.
## F18 — Navigation CLI commands

**Priority**: Medium
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Add CLI commands for ROS2 Nav2 navigation: `nav.go <label>` to navigate
to a detected object, `nav.cancel` to abort current goal, `nav.explore` to start
autonomous frontier exploration, and `nav.explore.stop` to stop it. Intent names use
consistent `navigation_*` / `exploration_*` prefixes.

## How to Demo
**Setup**: Robot running with Nav2 and dome_control behavior_manager.

**Steps**:
1. `nav go chair` — robot navigates to nearest "chair"
2. `nav cancel` — cancels in-progress goal
3. `nav explore` — starts frontier exploration
4. `nav explore stop` — stops exploration

**Expected output**: CLI prints `Intent published: navigation_go` (etc.); behavior_manager
receives and routes the intent to the Nav2 action server.
