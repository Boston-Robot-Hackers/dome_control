---
version: "1.0"
generated: "2026-05-06"
---

# VoiceInputNode

`voice_input_node.py` is now a ROS2 shell around the shared voice runtime. It
no longer owns wake-word detection or speech recognition directly; instead it
consumes a `VoiceTurn` from `control.voice.runtime`, maps the transcript to an
intent, and publishes the ROS messages that the rest of the system expects.

## Pipeline Shape

```text
IDLE
  -> runtime.next_turn()
  -> LISTENING (beep at wake)
  -> PROCESSING (map transcript)
  -> SPEAKING (beep or "say again")
  -> IDLE
```

The state topic remains a plain string topic because it is meant to be consumed
by simple listeners such as a UI, a light indicator, or logs.

## ROS Topics

| Topic | Direction | Type | Purpose |
|-------|-----------|------|---------|
| `/intent` | publish | `std_msgs/String` | Mapped intent JSON |
| `/voice/state` | publish | `std_msgs/String` | `IDLE` / `LISTENING` / `PROCESSING` / `SPEAKING` |
| `/announcement` | publish | `AnnouncementMsg` | Failure feedback |

The node only publishes an announcement on mapping failure. If the transcript is
recognized and mapped, it publishes the intent and leaves any higher-level
spoken response to the behavior manager or speech output node.

## Wake Callback

The runtime accepts a small callback that fires when wake is detected. The ROS
node uses that hook to publish `LISTENING` and play a short beep immediately.

```python
def on_wake(_wake):
    node.get_logger().info("Wake word detected — speak your command")
    node.publish_state("LISTENING")
    beep(frequency=880, duration=0.02, device_index=device_index)

turn = runtime.next_turn(ok_fn=rclpy.ok, on_wake=on_wake)
```

That keeps the runtime free of ROS imports while preserving the user-facing
timing of the listen state.

## Transcript Handling

```python
def process_turn(self, turn: VoiceTurn, device_index: int = 0) -> None:
    if turn.empty:
        self.publish_state("SPEAKING")
        speak("say again")
        self.publish_announcement("I didn't catch that")
        return
    self.process_transcript(turn.text, device_index=device_index)
```

The node has one job after the runtime returns: turn the transcript into a
normalized intent or a failure announcement. This is the layer where the voice
contract meets the rest of the robot.

## Observations

- The ROS loop still runs synchronously, so it does not process other callbacks
  while waiting on a voice turn.
- The `VOICE_DEVICE_INDEX` environment variable still selects the audio device.
  The value defaults to the runtime's capture card if the variable is not set.
- `SPEAKING` is still the published state name, although it mostly means
  "responding" now.
