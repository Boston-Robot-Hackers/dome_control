---
version: "2.0"
generated: "2026-05-06"
---

# VoiceInputNode

`voice_input_node.py` is the ROS2 shell around the shared voice runtime. It consumes a `VoiceTurn` from `control.voice.runtime`, maps the transcript to an intent, and publishes the ROS messages that the rest of the system expects.

## Pipeline Shape

```text
IDLE
  -> runtime.next_turn()        [blocks: wake detection + STT]
  -> LISTENING (beep 880 Hz at wake)
  -> PROCESSING (map transcript)
  -> SPEAKING (beep: 330 Hz success / 220 Hz empty)
  -> IDLE
```

## ROS Topics

| Topic | Direction | Type | Purpose |
|-------|-----------|------|---------|
| `/intent` | publish | `std_msgs/String` | Mapped intent JSON |
| `/voice/state` | publish | `std_msgs/String` | `IDLE` / `LISTENING` / `PROCESSING` / `SPEAKING` |

The node does not publish to `/announcement`. All spoken feedback is handled by `BehaviorManagerNode` or `SpeechOutputNode`. Empty/unrecognized turns produce only a low beep.

## Wake Callback

The runtime accepts a callback that fires when wake is detected. The node uses this hook to publish `LISTENING` and play a short beep immediately, before STT begins:

```python
def on_wake(_wake):
    node.get_logger().info("Wake word detected — speak your command")
    node.publish_state("LISTENING")
    beep(frequency=880, duration=0.02, device_index=device_index)

turn = runtime.next_turn(ok_fn=rclpy.ok, on_wake=on_wake)
```

## Transcript Handling

```python
def process_turn(self, turn: VoiceTurn, device_index: int = 0) -> None:
    if turn.empty:
        cmd = (turn.metadata or {}).get("command", {})
        self.get_logger().info(
            f"Empty turn: floor={cmd.get('floor'):.1f} cutoff={cmd.get('cutoff'):.1f} "
            f"started={cmd.get('command_started')} raw={cmd.get('raw_text')!r}"
        )
        self.publish_state("SPEAKING")
        beep(frequency=220, duration=0.15, device_index=device_index)
        return
    self.process_transcript(turn.text, device_index=device_index)
```

Empty turns log the silence floor, cutoff, whether speech was detected, and the raw Vosk transcript. This diagnostic helps distinguish mic level problems (low floor, speech never started) from grammar mismatch problems (speech started, but raw_text is empty or `[unk]`).

The 220 Hz / 150 ms buzz signals the user that the turn was not understood, without speaking (which would create acoustic feedback into the microphone).

```python
def process_transcript(self, text: str, device_index: int = 0) -> None:
    self.get_logger().info(f"Transcribed: '{text}'")
    self.publish_state("PROCESSING")
    intent = self.intent_mapper.map_intent(text)
    if intent:
        self.publish_intent(intent)
        self.publish_state("SPEAKING")
        beep(frequency=330, duration=0.02, device_index=device_index)
    else:
        self.publish_state("SPEAKING")
        beep(frequency=220, duration=0.15, device_index=device_index)
```

## Avoiding Acoustic Feedback

Earlier versions called `speak("say again")` and published spoken announcements for failures. Both created acoustic loops: the microphone would re-capture the spoken output and re-trigger the wake detector. Replacing speech responses with short beeps eliminates this path.

## Observations

- The ROS loop still runs synchronously, so it does not process other callbacks while waiting on a voice turn.
- `VOICE_DEVICE_INDEX` selects the capture device. It defaults to the runtime's `capture_card` if not set.
- `SPEAKING` is the published state name for both the success and failure paths — it means "responding" rather than literally speaking.
