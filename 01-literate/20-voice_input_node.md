---
version: "1.0"
generated: "2026-05-04"
---

# VoiceInputNode

`voice_input_node.py` wires the voice pipeline together into a ROS2 node. It coordinates `WakeWordDetector`, `SpeechTranscriber`, and `IntentMapper`, and publishes results to `/intent`, `/voice/state`, and `/announcement`.

## Pipeline State Machine

```
IDLE
  ↓ wake word detected
LISTENING  (beep at 880 Hz)
  ↓ transcribe() returns
PROCESSING
  ↓ intent mapped
SPEAKING   (beep at 330 Hz if intent found, else speak "say again")
  ↓
IDLE
```

State transitions are published to `/voice/state` as plain strings. Any node (e.g., a UI, a logging node) can subscribe to track what the voice pipeline is doing.

## Topic Layout

| Topic | Direction | Type | Purpose |
|-------|-----------|------|---------|
| `/intent` | publish | `std_msgs/String` | Mapped intent JSON |
| `/voice/state` | publish | `std_msgs/String` | IDLE/LISTENING/PROCESSING/SPEAKING |
| `/announcement` | publish | `AnnouncementMsg` | "I didn't catch that" |

The node publishes to `/announcement` only on failed recognition. Successful intents are published to `/intent` and the behavior manager is responsible for generating any announcement.

## Main Loop

```python
while rclpy.ok():
    detector.start()
    detected = detector.wait_for_wake(ok_fn=rclpy.ok)
    detector.stop()

    if not detected:
        break

    node.publish_state("LISTENING")
    beep(frequency=880, duration=0.02, device_index=device_index)

    text = transcriber.transcribe()
    node.process_transcript(text, device_index=device_index)
    node.publish_state("IDLE")
```

`detector.start()` and `detector.stop()` bracket each wake word listen cycle. The detector is stopped during transcription so the microphone stream is not shared between two consumers simultaneously.

`ok_fn=rclpy.ok` means the wake word loop exits cleanly when the ROS2 context shuts down (e.g., Ctrl+C). Without this, `wait_for_wake` would block indefinitely.

## Audio Feedback

Two beep tones provide auditory confirmation without requiring TTS synthesis:

- 880 Hz (high): "I'm listening" — plays immediately after wake word
- 330 Hz (low): "Intent received" — plays after successful mapping

On failed recognition, `speak("say again")` uses `espeak-ng` for a simple voice prompt.

## Observations

- The node does not call `rclpy.spin()` — it drives the executor manually via `wait_for_wake`'s `ok_fn=rclpy.ok` callback. This means ROS2 callbacks (subscriptions, service responses) are not processed during the wake word listen phase.
- `VOICE_DEVICE_INDEX` environment variable selects the audio device. On a Raspberry Pi with a USB microphone this is essential; the default device index `0` is often the wrong device.
- The node publishes `"SPEAKING"` before the actual speech/beep completes. Renaming this state to `"RESPONDING"` would be more accurate.
