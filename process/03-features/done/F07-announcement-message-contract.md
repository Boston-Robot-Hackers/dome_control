# Feature description for feature F07
## F07 — Announcement message contract migration
**Priority**: High
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Replace ad hoc `/announcement` payload handling with the
structured `Announcement.msg` contract (`text`, `priority`, `stamp`, `source`,
`dedup_key`, and priority constants). Update producers/consumers so speech output
and behavior logic use the same typed interface.

## How to Demo
**Setup**: ROS2 interfaces rebuilt with `Announcement.msg`.

**Steps**:
1. Start updated producers and `speech_output_node`
2. Publish representative announcement messages at different priorities
3. Verify message fields are populated and consumed correctly

**Expected output**: all announcement traffic uses `Announcement.msg`; no JSON
string assumptions remain on `/announcement`.
