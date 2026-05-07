# F16 — List Detected Objects

**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: New intent `list_objects` and CLI command `scene objects` that reads the latest
`/oak/detections` topic and speaks/prints the detected object labels and scores.
When oak is not running, reports "no detections available".

## How to Demo
**Setup**: Robot running with `bl control robot.launch.py oak:=true behavior:=true voice:=true`

**Steps**:
1. CLI: type `scene objects`
2. Voice: say "alexa objects"
3. Robot speaks detected objects via `/announcement`

**Expected output**: "I see: dog 0.91, person 0.85" or "No objects detected."
