# Tasks for Feature F09

## T01 — Subscribe to `/voice/state` in speech output
**Status**: not done
**Description**: Add state listener needed to react to `LISTENING`.

## T02 — Implement playback cancellation path
**Status**: not done
**Description**: Stop active synthesis/playback safely when barge-in is triggered.

## T03 — Define queue behavior on barge-in
**Status**: not done
**Description**: Decide whether interrupted items are dropped or requeued and
implement policy consistently.

## T04 — Add timing guardrails
**Status**: not done
**Description**: Ensure cancellation latency is low enough for practical voice UX.

## T05 — Add barge-in tests
**Status**: not done
**Description**: Validate cancel-on-listening behavior and post-cancel recovery.
