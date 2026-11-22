# Tasks for Feature F11

## T01 — Classify Piper/ALSA error handling
**Status**: partial
**Description**: `speech_output_node.on_announcement` already catches broad
synthesis/playback exceptions and logs `Speech output failed`, so a failed
announcement should not crash the node. Add explicit classification for Piper
synthesis failures, ALSA/aplay playback failures, WAV/gain failures, and config
validation failures.

## T02 — Add recovery behavior after transient failures
**Status**: not done
**Description**: Prove and, if needed, adjust the node so it resumes processing
subsequent announcements after a transient synthesis/playback error.

## T03 — Add speech-output metrics counters
**Status**: not done
**Description**: Track synthesis failures, playback failures, dropped
announcements, and, once F08 queueing exists, queue depth and preemptions.

## T04 — Add latency instrumentation for output stages
**Status**: not done
**Description**: Record synthesis time, playback start delay, playback duration,
and end-to-end output latency.

## T05 — Add reliability/observability tests
**Status**: not done
**Description**: Verify classified failure paths, post-failure recovery behavior,
and metric/log emission under normal and fault-injected conditions.
