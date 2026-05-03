---
title: "Voice and Control Architecture"
version: "1.1"
updated: "2026-04-23"
---

# Voice and Control Architecture

## Overview

Add a fully offline voice interface to the dome robot (Raspberry Pi 5–based differential drive
robot running ROS2 Jazzy). The interface supports a wake word, a finite command vocabulary, and
spoken responses. No cloud services, no Bluetooth, no free-form speech recognition.

---

## Requirements

- **Fully offline** — no cloud APIs, no internet dependency at runtime
- **Wake word detection** — robot ignores audio until it hears the trigger word
- **Structured command recognition** — a finite, predefined set of voice commands (not free-form STT)
- **Spoken responses** — robot replies with synthesized speech
- **Small and light** — hardware must be suitable for a mobile robot
- **ROS2 integration** — recognized intents published to robot control logic
- **No additional USB ports consumed** — HAT form factor preferred over USB peripherals
- **No Bluetooth** — wired audio only

---

## Architecture

### Audio Input
- **Hardware:** Seeed Studio ReSpeaker 2-Mics Pi HAT v2.0
- **Interface:** GPIO HAT (I2S), not USB
- **Driver:** TLV320AIC3104 codec, supported on Pi 5 via `seeed-linux-dtoverlays`

### Wake Word Detection
- **Software:** openWakeWord (open source, no account required)
- **Wake word:** **"hey jarvis"** or a custom model trained via openWakeWord tooling. "Jarvis" is acoustically distinctive (hard "J" onset, rare in casual English), will not conflict with household smart speakers, and reads naturally as a robot's name.
- **Runs:** locally on Pi 5 ARM, no cloud
- **Workflow:** listens continuously on ALSA device via `pyaudio`; fires callback on detection above confidence threshold, which transitions the voice state machine to LISTENING and hands audio off to Vosk

### Command Recognition
- **Software:** Vosk (open source, offline STT) + keyword/intent parser
- **Runs:** locally on Pi 5 ARM, no cloud
- **Workflow:** activates after wake word; records until silence; Vosk transcribes utterance to text; a lightweight keyword matcher maps text to a structured intent name + slots matching the intent table in this doc; unmatched utterances fall back to "I didn't catch that"
- **Model:** `vosk-model-small-en-us` (~40 MB) is sufficient for the finite command vocabulary; download once and deploy to Pi

### Speech Output
- **Software:** Piper TTS (open source, offline)
- **Hardware:** CQRobot 3W 8Ω speaker (ASIN B0738NLFTG) connected to ReSpeaker HAT's JST PH 2.0mm speaker header — plugs in directly, no adapter
- **Interface:** HAT's onboard Class-D amplifier handles audio out — no USB audio adapter needed
- **Voice model:** downloaded separately from Piper model repo (one-time setup)

### ROS2 Integration
- See the **Software Architecture** section below for the full node layout, ROS2 primitive choice, voice state machine, behaviors, safety, and design principles.
- High-level: voice is one of several **input** sources (future: buttons, screen, web UI). All inputs publish normalized `Intent` messages on `/intent`. A `behavior_manager_node` (the "brain") consumes intents, arbitrates, and invokes ROS2 services (queries) or actions (behaviors). State is published on topics consumed by any number of **output** sinks — speech, screen, LEDs. A separate reactive `safety_monitor_node` short-circuits motor commands on bumper / cliff / stall events.

---

## Voice Commands and Responses

This section defines the initial vocabulary of voice interactions. The list is expected to grow;
the structure (intents with slots) is designed to extend cleanly without changing the node
architecture.

### User → Robot: queries (answered synchronously)

| Intent | Example utterance | Slot(s) | Response |
|---|---|---|---|
| `describe_scene` | "what do you see?" | — | robot speaks a summary of detected objects |
| `count_objects` | "how many cans do you see?" | `object_type` | robot speaks the count |
| `get_battery` | "what's your battery level?" | — | robot speaks percentage |
| `get_location` | "where are you?" | — | robot speaks named location, or "I don't know" |

### User → Robot: behavior commands (long-running, cancellable)

| Intent | Example utterance | Slot(s) | Action |
|---|---|---|---|
| `start_exploring` | "start exploring" | — | launches exploration action |
| `stop` | "stop" / "halt" | — | cancels any running action (universal cancel) |
| `return_home` | "come back" / "go home" | — | navigates to dock |
| `go_to` | "go to the kitchen" | `location_name` | navigates to named location |
| `find_object` | "find the red can" | `object_type`, `attribute` | search behavior |
| `follow_me` | "follow me" | — | starts follow behavior |
| `be_quiet` | "be quiet" | — | cancels current TTS playback |
| `sleep` / `wake` | "go to sleep" / "wake up" | — | gates subsequent wake-word detection |

### Robot → User: spontaneous announcements

The speech output queue uses priority tiers; higher priority pre-empts lower.

| Announcement | Priority | Example text |
|---|---|---|
| Battery critical | safety | "my battery is low, I need to dock" |
| Stuck / immobile | safety | "I'm stuck, I can't move" |
| Lost (no localization) | status | "I am lost" |
| Can't proceed | status | "I can't go that way" |
| Finished exploring | status | "I finished exploring" |
| Found object | discovery | "I see a [object]" |
| No points of interest | discovery | "there is nothing in this room for me" |
| Awaiting input | chit-chat | "what do you want me to do next?" |
| Didn't understand | chit-chat | "I didn't catch that" |

### Slot vocabularies

Slot values are enumerated and shared across intents so the Rhino context stays small and
extending the vocabulary means editing a list, not retraining:

- `object_type`: can, bottle, person, chair, table, ball, … (extend as needed)
- `location_name`: kitchen, living room, hallway, dock, … (matched to map annotations)
- `attribute`: red, green, blue, small, large, … (optional qualifier)

---

## Software Architecture

The software stack is organized into four conceptual layers — **Input**, **Brain**, **Behaviors**, **Output** — plus a separate reactive **Safety** layer. Voice is one input among many; speech is one output among many. The brain is the only component that owns robot state and makes decisions, and it is independent of where intents come from or where state goes.

All inter-node communication uses structured ROS2 messages. Raw strings exist only at audio boundaries (mic in, speaker out).

### Layered node layout

```
  INPUT LAYER — any source of intent; publishes on /intent
  /intent is an open contract: any adapter that publishes Intent.msg is valid.
  source field ("voice"/"cli"/"rest"/"button") is for logging and arbitration only.

  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
  │ voice_input_node │ │ button_input_    │ │ cli_input_node   │ │ rest_api_node    │
  │ • Porcupine      │ │ node             │ │ • argparse CLI   │ │ • Flask/FastAPI  │
  │ • Rhino          │ │ • GPIO debounce  │ │ • REPL mode      │ │ • HTTP → Intent  │
  │ • /voice/state   │ │                  │ │ • scriptable     │ │                  │
  └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
           │                    │                    │                    │
           └────────────────────┼────────────────────┴────────────────────┘
                                ▼ /intent

  BRAIN — owns state, arbitrates, decides
  ┌─────────────────────────────────────────────────┐
  │ behavior_manager_node                           │
  │  • Subscribes /intent (source-agnostic)         │
  │  • Owns: current goal, active behavior,         │
  │    robot mode (awake/asleep, idle/busy)         │
  │  • Arbitrates concurrent / conflicting intents  │
  │  • Calls action clients, service clients        │
  │  • Publishes /robot_state, /announcement        │
  └──────────┬──────────────────┬───────────────────┘
             │                  │
         actions            services
  (explore, return_home,  (describe_scene,
   go_to, follow_me,       count_objects,
   find_object)            get_battery, get_location)

  BEHAVIORS LAYER — each non-trivial behavior is its own
  action server (see "Behaviors as composable actions" below)

  OUTPUT LAYER — any sink of state; subscribes to
  /robot_state, /announcement, /voice/state
  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
  │ speech_output_   │ │ display_node     │ │ led_node         │
  │ node             │ │ • renders pose,  │ │ • HAT RGB LEDs   │
  │ • Piper TTS      │ │   battery,       │ │ • mirrors voice  │
  │ • Priority queue │ │   current        │ │   state          │
  │ → speaker        │ │   behavior       │ │                  │
  └──────────────────┘ └──────────────────┘ └──────────────────┘

  SAFETY LAYER — reactive, runs in parallel
  ┌─────────────────────────────────────────────────┐
  │ safety_monitor_node                             │
  │  • Subscribes bumper, cliff, motor stall        │
  │  • On trigger: publishes zero-velocity /cmd_vel │
  │    (preempts Nav2 and any active behavior)      │
  │  • Notifies brain via /status/stuck etc.        │
  └─────────────────────────────────────────────────┘
```

### ROS2 primitive choice

- **Services** for synchronous queries: `describe_scene`, `count_objects`, `get_battery`, `get_location`. The brain calls the service, receives the answer, formats a spoken reply, and publishes an `/announcement`.
- **Actions** for long-running, cancellable behaviors: `explore`, `return_home`, `go_to`, `follow_me`, `find_object`. Actions provide feedback during execution and can be cancelled cleanly — essential for "stop" to work universally.
- **Topics** for asynchronous events:
  - `/intent` — normalized intents from any input source
  - `/voice/state` — voice node state (idle / listening / etc.)
  - `/robot_state` — the brain's view: pose, battery, current behavior, mode
  - `/announcement` — spoken-text-to-queue, with priority tier
  - `/status/battery_low`, `/status/lost`, `/status/stuck` — reactive status events
  - `/discovery/object_found` — perception events

### Message definitions

Two custom message types carry all inter-layer communication. Raw speech strings live only at audio boundaries.

`Intent.msg` — published on `/intent` by any input source:

    string name                        # e.g. "start_exploring", "count_objects", "stop"
    string source                      # "voice", "button", "web" — for logging and arbitration
    builtin_interfaces/Time stamp
    diagnostic_msgs/KeyValue[] slots   # optional slot name/value pairs
    float32 confidence                 # 0.0–1.0; voice sets this from Rhino, deterministic sources set 1.0

`Announcement.msg` — published on `/announcement` by the brain or any node that wants to speak:

    string text                        # the text to speak
    uint8 priority                     # see constants below
    builtin_interfaces/Time stamp
    string source                      # originating node name, for debugging
    string dedup_key                   # optional; suppresses duplicates within a window

    uint8 PRIORITY_SAFETY      = 0     # highest — battery critical, stuck
    uint8 PRIORITY_STATUS      = 1     # lost, finished, can't proceed
    uint8 PRIORITY_QUERY_REPLY = 2     # answer to a user query
    uint8 PRIORITY_ACTION_ACK  = 3     # "okay, exploring"
    uint8 PRIORITY_DISCOVERY   = 4     # "I see a can"
    uint8 PRIORITY_CHITCHAT    = 5     # lowest — filler

Notes:

- `diagnostic_msgs/KeyValue` is part of the standard ROS2 distribution — no need to define a custom key-value type for slots.
- Slot values travel as strings; each behavior parses them as needed (e.g., numeric counts are parsed on the consumer side).
- `dedup_key` lets `speech_output_node` suppress repeated identical announcements within a configurable window (e.g., avoid saying "I am lost" every second).

### Voice state machine

```
  IDLE ──"Jarvis"──▶ LISTENING ──intent──▶ PROCESSING ──reply──▶ SPEAKING ──done──▶ IDLE
                         │                       │
                         └── timeout ──▶ ERROR ──┘
                                          │
                                          └──▶ "I didn't catch that" ──▶ IDLE
```

This state is local to `voice_input_node` and published on `/voice/state`. Display and LED nodes subscribe for feedback.

### Behaviors as composable actions

Non-trivial behaviors live in their own action-server nodes, not inside the brain. The brain invokes them via action clients and waits for completion or cancellation. For simple behaviors (e.g. `go_to`) this is a thin wrapper around Nav2. For complex behaviors, the action server internally uses a **behavior tree** to orchestrate sub-actions.

Example: `explore` as a behavior tree:

```
  explore (root, sequence, loops until done)
    ├── select_next_frontier    (service call)
    ├── navigate_to_point       (Nav2 action)
    ├── look_around             (rotate + scan)
    ├── record_objects_seen     (service call)
    └── check_if_done           (condition — breaks loop if true)
```

The brain doesn't see any of this. It called `explore` and will hear back when the action succeeds or is cancelled. The `explore` node internally handles retries, failure recovery, and resumption — keeping complexity out of the brain.

**Committed BT library: `py_trees_ros`.** Rationale: Python matches the rest of the stack (Picovoice and Piper are both Python), ceremony is low for prototyping, documentation and community are solid, and its runtime maps cleanly onto ROS2 actions and topics. If a specific behavior later needs the performance or Nav2-native BT format of **BehaviorTree.CPP**, that one behavior can be ported without rewriting the rest. **YASMIN** or **SMACH** remain fallback options for any behavior that is clearly a flat state machine rather than a tree.

### Reactive safety layer

Safety reflexes (bumper pressed, cliff detected, motor stall) must have lower latency than the brain's decision loop and must not wait for ongoing planning. They live in a dedicated `safety_monitor_node` that:

- Subscribes directly to sensor topics (bumper, cliff, motor current / stall).
- On trigger, publishes zero-velocity `Twist` messages to `/cmd_vel`, preempting whatever Nav2 or any active behavior was sending.
- Notifies the brain after the fact via `/status/stuck` (or equivalent) so the brain can cancel the active behavior, announce the problem, and decide what to do next.

This is the classic subsumption split: **reactive** (fast, reflexive) below **deliberative** (slow, planning). The brain never needs to know a bumper exists.

### Design principles

- **Input/output symmetry.** Any input source (voice, button, screen, web) produces the same normalized `Intent`. Any output sink (speech, screen, LEDs) consumes the same state topics. Swapping or adding either side is a new node, not a refactor.
- **The brain is source-agnostic and sink-agnostic.** It doesn't know where intents came from or where announcements go. This keeps it reusable and testable.
- **Priority-queued TTS.** `speech_output_node` is the only path to the speaker. Priority tiers (safety > status > query reply > action ack > discovery > chit-chat) prevent overlapping or out-of-order speech.
- **Barge-in is first-class.** If the wake word fires during TTS, `speech_output_node` cancels playback on seeing `/voice/state = LISTENING`. The user can always interrupt the robot.
- **Universal cancel.** "Stop" maps to "cancel the currently running action" in the brain — handled once, not duplicated per behavior. A button-press "stop" produces the same intent as a voice "stop."
- **Slots, not separate intents.** "How many cans?" and "how many bottles?" are one `count_objects` intent with an `object_type` slot.
- **Debounce spontaneous announcements at the source.** Each status publisher rate-limits itself before publishing.
- **Graceful degradation.** Failed Rhino match → "I didn't catch that" → idle. Failed TTS → log and recover. Disconnected mic → node restarts capture.
- **Structured messages between nodes.** `Intent.msg` (intent name + slots) carries input. `Announcement.msg` (text + priority tier) carries output. Raw strings live only at audio boundaries.
- **Reactive safety is separate from deliberation.** Reflexes short-circuit the brain; the brain reacts afterward.
- **Algorithm logic is separate from ROS2 plumbing.** The brain's arbitration rules, state machine, and intent dispatch live in a pure Python `BehaviorManager` class. `behavior_manager_node` is a thin ROS2 shell that receives `Intent` messages, calls `BehaviorManager`, and publishes the results. This means the arbitration logic can be unit-tested with plain pytest — no ROS2 environment required. The same principle applies to any non-trivial behavior: the behavior tree or state machine lives in a pure Python class; the action server node is just the ROS2 entry point.

---

## I2C Bus Notes

The TLV320AIC3104 codec sits on the Pi's I2C bus at fixed address **0x18**. This address
has been verified as unoccupied on the dome robot's existing I2C bus. The HAT is compatible
with sharing the bus via the existing I2C shim.

---

## Parts List

### New hardware (voice interface additions)

| Item | Notes | Link | Est. Price |
|---|---|---|---|
| Seeed Studio ReSpeaker 2-Mics Pi HAT **v2.0** | Must be v2.0 (TLV320AIC3104 chip) — v1.0 (WM8960) has Pi 5 driver issues. Handles mic input AND speaker output via onboard Class-D amp. ⚠️ The Amazon listing (B0G18R19PY) has a garbled third-party title — verify the chip is TLV320AIC3104 before buying. Seeed Studio direct is safer. | [Amazon (B0G18R19PY)](https://www.amazon.com/dp/B0G18R19PY) · [Seeed direct](https://www.seeedstudio.com/ReSpeaker-2-Mics-Pi-HAT.html) | ~$15 |
| CQRobot 3W 8Ω Speaker, JST-PH2.0 (70×31×16mm) | 8Ω, JST-PH2.0 connector plugs directly into HAT's JST PH 2.0mm speaker port — no adapter needed. Stock cable ~15cm. Has mounting screw holes (24×63mm spacing). | [Amazon (B0738NLFTG)](https://www.amazon.com/dp/B0738NLFTG) | ~$9 |
| JST PH 2.0mm 2-pin extension cable *(optional)* | Only needed if speaker is mounted more than ~15cm from the HAT. Comes as male+female pair; use female end on HAT, male end on speaker. | [Amazon — XUGERIP 20-pair kit](https://www.amazon.com/dp/B0D9R33S9T) | ~$8 |
| GPIO stacking header, 2×20 pin *(conditional)* | Only needed if the robot already has a HAT on the Pi's 40-pin GPIO. Adafruit's extra-long version clears most HAT components. | [Amazon — Adafruit extra-long](https://www.amazon.com/dp/B00TW0W9HQ) | ~$3 |
| M2.5 brass standoffs + screws, 20-pack *(conditional)* | Secures HAT at correct height above Pi. Often already on the robot; verify before ordering. Geekworm kit includes M2.5 × 11mm standoffs, screws, and nuts. | [Amazon — Geekworm 20-pack](https://www.amazon.com/dp/B0721SP83Q) | ~$6 |
| 3M VHB foam tape or M2 screws | Mounts speaker to robot chassis. VHB tape (1/2" wide) is faster and holds well for a passive speaker. M2 screws fit the CQRobot mounting holes. | Hardware store or Amazon | ~$1–3 |

**Total new hardware cost: ~$24 (base: HAT + speaker) to ~$44 (with extension cable, stacking header, standoffs)**

### GPIO conflict check *(required before ordering)*

The ReSpeaker HAT occupies the following Pi GPIO pins. If the dome robot's existing
motor controller or other HATs use any of these, a stacking header alone will not
resolve the conflict — pin assignment remapping or a different audio solution would
be required.

| HAT function | Pins used |
|---|---|
| I2S audio (codec) | GPIO 18, 19, 20, 21 |
| I2C (codec config) | GPIO 2, 3 (I2C-1) |
| SPI (RGB LEDs) | GPIO 10, 11 (SPI0) |
| User button | GPIO 17 |
| Grove digital port | GPIO 12, 13 |

Most differential drive motor controllers use PWM and direction pins that do not
overlap with the above. Verify against the specific motor HAT before assembly.

### Software (free, no hardware cost)

| Component | Source | Notes |
|---|---|---|
| openWakeWord | github.com/dscripka/openWakeWord | Open source, no account; custom or pre-trained wake word models |
| Vosk | alphacephei.com/vosk | Open source offline STT; `vosk-model-small-en-us` ~40 MB |
| Piper TTS | github.com/rhasspy/piper | Open source; download voice model file separately (~50–130 MB) |
| seeed-linux-dtoverlays | github.com/Seeed-Studio/seeed-linux-dtoverlays | Device tree overlay for ReSpeaker HAT on Pi 5 |

### Pre-existing (not included in cost)

| Item | Note |
|---|---|
| Raspberry Pi 5 | Already on robot |
| Pi 5 USB-C power supply (27W recommended) | Already on robot; HAT draws from Pi's 5V GPIO rail — no separate supply needed |
| Motor controller and wiring | Already on robot; verify GPIO pins per table above |
| MicroSD card (32 GB+) | Already on robot |

---

## What Was Explicitly Rejected

| Item | Reason |
|---|---|
| USB mic array | Wastes a USB port; heavier; no benefit over HAT |
| USB-powered desktop speakers (e.g. Creative Pebble) | Too large and heavy for mobile robot |
| Adafruit USB Audio Adapter | Unnecessary — HAT has onboard DAC/audio out |
| MAX98357 I2S amplifier board | Only needed without the ReSpeaker HAT; redundant here |
| Picovoice Porcupine + Rhino | Requires account signup; Picovoice blocks personal/educational email addresses — not accessible for this project |
| Free-form speech recognition (e.g. Whisper always-on) | Too heavy for always-on wake-word detection; Vosk + keyword matcher is sufficient and far lighter |

---

## Open Items / Next Steps

Organized by phase so work can proceed with clear dependencies. Later phases depend on earlier ones.

### Phase 1 — Hardware and host setup
- [ ] Order hardware (ReSpeaker HAT v2.0, 3 W 8 Ω speaker)
- [ ] Verify connector compatibility (XH2.54 on HAT vs. speaker connector)
- [ ] Install `seeed-linux-dtoverlays`; verify HAT recognized by ALSA on Pi 5
- [ ] Install `openWakeWord` and `vosk` in the dome-voice venv; download `vosk-model-small-en-us`
- [ ] Download a Piper voice model (one-time)

### Phase 2 — Message and interface definitions
- [ ] Define `Intent.msg` (fields per *Message definitions* section)
- [ ] Define `Announcement.msg` with priority constants
- [ ] Define service definitions: `DescribeScene.srv`, `CountObjects.srv`, `GetBattery.srv`, `GetLocation.srv`
- [ ] Define action definitions: `Explore.action`, `ReturnHome.action`, `GoTo.action`, `FollowMe.action`, `FindObject.action`

### Phase 3 — Voice and speech
- [ ] Define keyword/intent mapping table in code to match the intent and slot tables in this doc
- [ ] Implement `voice_input_node` — openWakeWord (wake = "Jarvis") + Vosk STT + keyword matcher; publishes `/intent`, `/voice/state`; enforces listen timeout; falls back to "I didn't catch that"
- [ ] Implement `speech_output_node` — Piper TTS with priority queue; barge-in on `/voice/state = LISTENING`; dedup by `dedup_key`
- [ ] Smoke test: say "Jarvis, what's your battery level?" → stubbed brain answers → spoken reply

### Phase 4 — Brain and behaviors
- [ ] Install `py_trees_ros` on Pi 5; verify hello-world BT
- [ ] Implement `behavior_manager_node` (brain) — subscribes `/intent`; owns robot state; invokes actions/services; handles universal `stop` as action cancel
- [ ] Implement stub service servers for the four queries (returning dummy data) to unblock voice testing
- [ ] Implement `explore` action server with a `py_trees_ros` behavior tree (frontier select → Nav2 navigate → look around → record objects → done check)
- [ ] Implement `return_home`, `go_to` action servers (thin Nav2 wrappers)
- [ ] Implement `follow_me`, `find_object` action servers (can stub initially)

### Phase 5 — Additional inputs and outputs
- [ ] Implement `button_input_node` — GPIO stop button publishes `stop` intent on `/intent`
- [ ] Implement `display_node` — subscribes `/robot_state`; renders pose, battery, current behavior
- [ ] Implement `led_node` — HAT RGB LEDs mirror `/voice/state`

### Phase 6 — Safety layer
- [ ] Implement `safety_monitor_node` — subscribes bumper/cliff/stall topics; publishes zero-velocity `/cmd_vel` on trigger; notifies brain via `/status/stuck`
- [ ] Integration test: bumper press during `explore` → motors stop, brain cancels behavior, robot announces "I'm stuck"

### Phase 7 — End-to-end validation
- [ ] Scenario: "Jarvis, start exploring" → action runs → "Jarvis, stop" → action cancels cleanly
- [ ] Scenario: robot mid-utterance → wake word fires → TTS cancels, robot listens (barge-in)
- [ ] Scenario: low battery during explore → safety announcement pre-empts any discovery chatter
- [ ] Scenario: Rhino fails to match → "I didn't catch that" → back to idle
- [ ] Scenario: button press while exploring → same effect as voice "stop"
