# Feature description for feature F05
## F05 — Voice pipeline performance instrumentation
**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Add end-to-end timing instrumentation for the voice input path
to identify latency bottlenecks between wake-word detection, capture start,
transcription, intent mapping, and publish. The goal is to collect precise
per-stage timing data and summary stats (p50/p95/max) so we can determine which
part of the pipeline is slow before optimizing.

## How to Demo
**Setup**: Voice stack running on target hardware with logging enabled and
instrumentation flag/config turned on.

**Steps**:
1. Start `ros2 run control voice_input` with instrumentation enabled
2. Trigger wake word and run a sequence of recognized and unrecognized commands
3. Collect timing logs/metrics output for each interaction
4. Review per-stage latency and aggregated summary stats

**Expected output**: logs/metrics clearly show latency by stage (wake detect,
listen window, STT, intent mapping, publish/announcement) and identify dominant
contributors to total response time.
