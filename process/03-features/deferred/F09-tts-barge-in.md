# Feature description for feature F09
## F09 — TTS barge-in on voice listen state
**Priority**: High
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Implement barge-in behavior so active speech playback is
cancelled when `/voice/state` transitions to `LISTENING`. This ensures wake word
and user speech can always interrupt robot output.

## How to Demo
**Setup**: `voice_input_node` and `speech_output_node` running; TTS playback active.

**Steps**:
1. Trigger an announcement long enough to keep TTS speaking
2. Trigger wake word so voice state becomes `LISTENING`
3. Confirm TTS is cancelled immediately

**Expected output**: playback stops promptly on `LISTENING`; node remains healthy
and can resume future announcements after interaction completes.
