# Tasks for Feature F05

## T01 — Define timing points and metric schema
**Status**: not done
**Description**: Define exactly which timestamps are captured and how they map
to metrics: wake detection latency, post-wake capture start delay, STT duration,
intent mapping duration, publish duration, and total turn latency. Include
correlation ID per interaction so one voice turn can be traced end-to-end.

## T02 — Add instrumentation hooks to voice_input_node flow
**Status**: not done
**Description**: Add instrumentation calls at each defined timing point in the
voice state machine (`IDLE -> LISTENING -> PROCESSING -> SPEAKING -> IDLE`)
without changing behavior. Emit structured timing records with interaction IDs.

## T03 — Instrument wake-word detector timing
**Status**: not done
**Description**: Add timing around detector start, first frame read, detection
event, and detector stop to isolate wake-word path overhead and debounce impact.

## T04 — Instrument STT timing
**Status**: not done
**Description**: Add timing around capture open, first audio chunk received,
utterance end detection, Vosk decode completion, and final transcript return.

## T05 — Add aggregated latency summaries
**Status**: not done
**Description**: Add rolling summary output (count, p50, p95, max) for each stage
and total latency so bottlenecks are visible without external tooling.

## T06 — Add config controls for instrumentation
**Status**: not done
**Description**: Add env vars/params to enable instrumentation, control log
verbosity, and set summary interval. Ensure default mode keeps normal logs clean.

## T07 — Add tests for instrumentation behavior
**Status**: not done
**Description**: Add tests that validate timing hooks fire in expected order,
interaction IDs propagate across stages, and instrumentation can be disabled.
Tests should verify no functional behavior changes to existing intent flow.

## T08 — Document analysis workflow
**Status**: not done
**Description**: Document how to run the instrumented node, gather timing output,
and interpret results to pinpoint whether slowdown is dominated by wake-word,
capture, STT decode, mapping, or publish/announcement stages.
