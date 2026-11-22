# Feature description for feature F11
## F11 — Voice output reliability and observability
**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Improve speech output failure handling and instrumentation.
`speech_output_node` currently catches broad synthesis/playback exceptions in
`on_announcement` and logs `Speech output failed`, so a failed announcement should
not crash the node. This feature adds the missing production-grade reliability
pieces: classify Piper vs ALSA/playback failures, prove recovery for subsequent
announcements, and expose operational metrics (queue depth once F08 exists,
drops, preemptions, synthesis failures, playback failures, latency) to diagnose
output quality and responsiveness.

## How to Demo
**Setup**: `speech_output_node` with observability enabled; fault injection path
for Piper/ALSA errors available.

**Steps**:
1. Run normal announcement traffic and inspect runtime metrics/logs
2. Trigger controlled playback/synthesis failure
3. Verify node recovers and continues processing new announcements

**Expected output**: failures are logged with classified context, counters update,
and the speech pipeline demonstrably continues operating after transient faults.
