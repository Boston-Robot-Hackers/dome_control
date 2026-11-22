# Feature description for feature F10
## F10 — Announcement dedup and suppression windows
**Priority**: Medium
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Implement `dedup_key`-based suppression in `speech_output_node`
so repeated announcements within a configurable time window are dropped. This
reduces repetitive chatter while preserving high-priority alerts.

## How to Demo
**Setup**: `speech_output_node` with dedup enabled and configurable window.

**Steps**:
1. Publish repeated announcements with the same `dedup_key`
2. Publish a different `dedup_key` announcement during the same period
3. Repeat after dedup window expires

**Expected output**: duplicates inside the suppression window are dropped; new
keys or expired-window entries are spoken.
