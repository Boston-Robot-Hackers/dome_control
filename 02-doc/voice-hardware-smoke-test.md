# Voice Hardware Smoke Test

Goal: get from newly received hardware to one real spoken interaction as quickly
as possible, without waiting for the full `Intent.msg`, behavior tree, or
navigation architecture.

Hardware target:
- Raspberry Pi 5
- Seeed ReSpeaker 2-Mics Pi HAT v2.0, TLV320AIC3104 codec
- Wired 3 W / 8 ohm speaker connected to the HAT speaker output

Primary references:
- Seeed v2 setup: https://wiki.seeedstudio.com/respeaker_2_mics_pi_hat_raspberry_v2/
- openWakeWord: https://github.com/dscripka/openWakeWord
- Vosk: https://alphacephei.com/vosk/

## Phase 0 — Physical Check

Before powering the Pi:
1. Confirm the HAT is v2.0. The intended codec is TLV320AIC3104.
2. Confirm no existing robot board uses GPIO 18, 19, 20, 21, 2, 3, 10, 11, 17,
   12, or 13.
3. Seat the HAT squarely on the 40-pin header.
4. Connect the speaker to the HAT speaker output.

## Phase 1 — Make ALSA See the HAT

Run on the Pi, not on the Mac:

```bash
sudo apt update
sudo apt install -y git build-essential flex bison libssl-dev bc libncurses5-dev libncursesw5-dev
git clone https://github.com/Seeed-Studio/seeed-linux-dtoverlays.git
cd seeed-linux-dtoverlays
make overlays/rpi/respeaker-2mic-v2_0-overlay.dtbo
sudo cp overlays/rpi/respeaker-2mic-v2_0-overlay.dtbo /boot/firmware/overlays/respeaker-2mic-v2_0.dtbo
echo "dtoverlay=respeaker-2mic-v2_0" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

After reboot:

```bash
aplay -l
arecord -l
```

Expected: both commands show a `seeed2micvoicec` card. On this robot it is
card 0, device 0.

## Phase 2 — Prove Speaker and Mic

Set mixer levels:

```bash
alsamixer
```

Use F6 to select the Seeed device, then set speaker and capture levels.
Useful settings: `PCM 100%`, `Line 9 unmute`, `Line DAC 100%`, `PGA 60-70`,
`ADC HPF Cut-off 0.0125xFs`.

Replace `0,0` below with the actual card/device from `aplay -l` and `arecord -l`:

```bash
speaker-test -D plughw:0,0 -c 2 -t wav
arecord -D plughw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/respeaker-test.wav
aplay -D plughw:0,0 /tmp/respeaker-test.wav
```

Pass condition:
- `speaker-test` is audible.
- The recorded WAV contains intelligible speech.

Stop here and fix ALSA/mixer issues before touching ROS2 or voice deps.

## Phase 3 — Install Voice Dependencies

Install into system Python so `ros2 run` works without venv activation:

```bash
sudo apt install -y python3-pyaudio
pip3 install openwakeword vosk --break-system-packages
```

Download the Vosk small English model:

```bash
mkdir -p ~/models
cd ~/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

## Phase 4 — Prove Wake Word

Save as `/tmp/wake_test.py` and run `python3 /tmp/wake_test.py 2>/dev/null`:

```python
import pyaudio
import numpy as np
from openwakeword.model import Model
import os

oww_dir = os.path.dirname(__import__("openwakeword").__file__)
MODEL_PATH = os.path.join(oww_dir, "resources", "models", "hey_jarvis_v0.1.onnx")

model = Model(wakeword_model_paths=[MODEL_PATH])
pa = pyaudio.PyAudio()
stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                 input=True, frames_per_buffer=1280, input_device_index=0)
print("Listening — say 'Hey Jarvis'")
while True:
    audio = np.frombuffer(stream.read(1280, exception_on_overflow=False), dtype=np.int16)
    score = list(model.predict(audio).values())[0]
    if score > 0.5:
        print(f"Wake word detected! score={score:.2f}")
```

Pass condition: saying "Hey Jarvis" prints detection events with score > 0.5.

If the wrong input device is selected, list devices first:

```python
import pyaudio
pa = pyaudio.PyAudio()
for i in range(pa.get_device_count()):
    print(i, pa.get_device_info_by_index(i)['name'])
```

Then set `input_device_index` to the index of `seeed2micvoicec`.

## Phase 5 — Run the ROS2 Voice Node

```bash
cd ~/ros2_ws
colcon build --packages-select control
source install/setup.bash
export VOSK_MODEL_PATH=/home/pitosalas/models/vosk-model-small-en-us-0.15
ros2 run control voice_input 2>/dev/null
```

In a second terminal, monitor intents:

```bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /intent
```

Say "Hey Jarvis" then a command such as "what do you see" or "stop".

Pass condition: `/intent` receives a structured JSON intent matching the spoken
command. `/voice/state` transitions IDLE → LISTENING → PROCESSING → IDLE.

If the wrong audio device is used, set before running:

```bash
export VOICE_DEVICE_INDEX=0
```

## Phase 6 — Speech Output

For the first speaker proof, ALSA playback is enough. For robot speech:

1. Install Piper TTS.
2. Download one small English voice model.
3. Implement `speech_output_node` subscribing to `/announcement`.
4. Generate a WAV into `/tmp`, then play it through the Seeed ALSA device.

Keep barge-in, priorities, and dedup for the second pass. The first pass should
only prove that `/announcement` becomes audible speech.

## Fastest Useful Demo

Minimum successful demo:

1. `aplay -l` and `arecord -l` show `seeed2micvoicec`.
2. A recorded WAV plays back through the robot speaker.
3. Wake word test script detects "Hey Jarvis".
4. `ros2 run control voice_input` publishes a structured intent on `/intent`
   when wake word + command are spoken.
