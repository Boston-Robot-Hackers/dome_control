# Feature description for feature F08
## F08 — TTS priority queue and preemption
**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Add queueing and preemption behavior in `speech_output_node`
using priority tiers from `Announcement.msg`. Higher-priority announcements must
interrupt or bypass lower-priority speech to keep safety and status speech timely.

## How to Demo
**Setup**: `speech_output_node` with queue support, announcement producers active.

**Steps**:
1. Publish low-priority chatter announcements
2. While speaking, publish a safety-priority announcement
3. Observe queue ordering and interruption behavior

**Expected output**: safety/status speech pre-empts lower-priority speech and is
played first; ordering is deterministic within each priority.
