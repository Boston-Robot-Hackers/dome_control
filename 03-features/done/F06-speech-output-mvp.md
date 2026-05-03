# Feature description for feature F06
## F06 — Speech output node MVP (Piper + ALSA)
**Priority**: High
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Implement the first-pass `speech_output_node` that subscribes to
`/announcement`, synthesizes speech with Piper, writes WAV output to a
configurable temp directory, and
plays audio through the ReSpeaker/ALSA output device. This is the minimum path
to make announcements audible on robot hardware.

## How to Demo
**Setup**: Piper installed, one English Piper model downloaded, ALSA output
device verified (`seeed2micvoicec`).

**Steps**:
1. Start `speech_output_node`
2. Publish an `/announcement` message with test text
3. Confirm WAV generation and playback on the robot speaker

**Expected output**: spoken audio is heard for each announcement input and node
continues running after playback.
