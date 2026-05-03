# Tasks for Feature F11

## T01 — Add robust Piper/ALSA error handling
**Status**: not done
**Description**: Catch and classify synthesis/playback failures without crashing
the node.

## T02 — Add recovery behavior after transient failures
**Status**: not done
**Description**: Ensure the node can resume processing subsequent announcements
after an error.

## T03 — Add speech-output metrics counters
**Status**: not done
**Description**: Track queue depth, dropped announcements, preemptions, synthesis
failures, and playback failures.

## T04 — Add latency instrumentation for output stages
**Status**: not done
**Description**: Record synthesis time, playback start delay, playback duration,
and end-to-end output latency.

## T05 — Add reliability/observability tests
**Status**: not done
**Description**: Verify failure paths, recovery behavior, and metric/log emission
under normal and fault-injected conditions.
