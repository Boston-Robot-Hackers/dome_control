# Tasks for Feature F10

## T01 — Implement dedup cache keyed by `dedup_key`
**Status**: not done
**Description**: Track recent keys with timestamps and configurable suppression
window.

## T02 — Apply dedup policy by priority
**Status**: not done
**Description**: Ensure safety-critical announcements are not unintentionally
suppressed.

## T03 — Add configuration for dedup windows
**Status**: not done
**Description**: Add defaults and per-priority/per-source overrides if needed.

## T04 — Emit dedup diagnostics
**Status**: not done
**Description**: Log/counter when announcements are dropped by dedup logic.

## T05 — Add dedup tests
**Status**: not done
**Description**: Validate within-window suppression and post-window replay.
