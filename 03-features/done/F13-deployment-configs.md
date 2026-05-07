# Feature description for feature F13
## F13 — Multi-machine deployment configurations
**Priority**: Medium
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Support running control package nodes across multiple deployment
configurations via two parameterized launch files. Hardware-locked nodes stay on
the robot; pure-logic nodes can run anywhere. ROS2 DDS handles cross-machine
routing transparently — no code changes needed, only launch infrastructure.

**Status**: Complete. `launch/robot.launch.py` and `launch/remote.launch.py`
created and installed via CMakeLists. Both registered in `launch_templates`
config.

## Architecture

Stable interface boundary — two topics:

```
[input source]  →  /intent (std_msgs/String JSON)  →  behavior_manager
behavior_manager  →  /announcement (AnnouncementMsg)  →  speech_output_node
```

Any source publishing valid JSON to `/intent` works regardless of machine.

## Node Placement

| Node | Hardware dependency | Default location |
|------|-------------------|-----------------|
| `speech_output` | piper binary + ALSA + speaker | onboard (locked) |
| `describe_scene_stub` | robot camera data | onboard (locked) |
| `behavior_manager` | none — pure logic | onboard (default, moveable) |
| `voice_input` | mic | follows mic hardware |
| `rf_input` (future) | RF receiver | follows RF hardware |
| CLI (`run`) | none | offboard (interactive, not a launch file) |

## Launch Files

Two launch files, both in `launch/`:

### `robot.launch.py`
Always starts: `speech_output`, `describe_scene_stub`
Args:
- `--voice False` — set true if mic is physically on robot
- `--behavior True` — set false to move behavior_manager offboard

### `remote.launch.py`
Args:
- `--voice True` — set false if mic is onboard or not used
- `--behavior False` — set true to run behavior_manager offboard

### Common invocations

```bash
# Config A — everything onboard, mic on robot
bl control robot.launch.py --voice True

# Config B — mic offboard, everything else onboard
# robot:    bl control robot.launch.py
# offboard: bl control remote.launch.py

# Config D — CLI offboard, no voice
# robot:    bl control robot.launch.py
# offboard: ros2 run control run   (interactive, not a launch file)

# Config E — behavior_manager offboard
# robot:    bl control robot.launch.py --behavior False
# offboard: bl control remote.launch.py --behavior True --voice False
```

## Known Wart

`voice_input_node` calls `beep()` and `speak()` via local audio, not `/announcement`.
In config B, feedback audio plays on offboard machine. Acceptable for operator-present
setup. Fix later by routing through `/announcement` if robot-side feedback needed.

## What Needs Building

1. `launch/robot.launch.py` — `speech_output` + `describe_scene_stub` always;
   `voice_input` and `behavior_manager` conditional on args.
2. `launch/remote.launch.py` — `voice_input` and `behavior_manager` conditional on args.
3. `CMakeLists.txt` update — install `launch/` directory.
4. `rf_input_node` — future, hardware TBD. Publishes to `/intent`. Implement when hardware chosen.

## Required Env Vars Per Node

| Node | Env var | Purpose |
|------|---------|---------|
| `speech_output` | `PIPER_BIN` | path to piper binary |
| `speech_output` | `PIPER_MODEL_PATH` | path to .onnx voice model |
| `speech_output` | `SPEECH_ALSA_DEVICE` | ALSA device string (optional) |
| `speech_output` | `SPEECH_GAIN` | volume scale factor (default 0.35) |
| `speech_output` | `PIPER_LENGTH_SCALE` | speech rate (default 1.25) |
| `voice_input` | `VOICE_DEVICE_INDEX` | mic device index (default 0) |
| `rf_input` | TBD | depends on hardware |

## How to Demo

**Setup**: Two machines, same network, same `ROS_DOMAIN_ID`. ROS2 sourced on both.

**Steps** (config B — mic offboard, speaker on robot):
1. Robot: `bl control robot.launch.py`
2. Offboard: `bl control remote.launch.py`
3. Speak wake word and command into offboard mic.

**Expected output**: intent published from offboard, behavior_manager on robot
receives it, announcement published, speech plays through robot speaker.
