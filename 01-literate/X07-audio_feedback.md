---
version: "1.0"
generated: "2026-05-04"
---

# Audio Feedback (Appendix)

`audio_feedback.py` provides two lightweight audio feedback functions for voice state transitions.

## beep

```python
def beep(frequency: int = 880, duration: float = 0.15, device_index: int = 0) -> None:
    sample_rate = 16000
    t = np.arange(int(sample_rate * duration)) / sample_rate
    samples = (np.sin(2 * math.pi * frequency * t) * 32767 * 0.05).astype(np.int16)
    # open PyAudio stream, write samples, close
```

Generates a pure sine wave at the given frequency. Amplitude is 5% of full scale (`* 0.05`) — intentionally quiet so it doesn't overwhelm speech. Used at 880 Hz ("listening") and 330 Hz ("intent received") in `VoiceInputNode`.

## speak

```python
def speak(text: str, speed: int = 150, amplitude: int = 15) -> None:
    subprocess.run(["espeak-ng", "-s", str(speed), "-a", str(amplitude), text], ...)
```

Calls `espeak-ng` for simple TTS. Used only for the "say again" fallback — the primary TTS pipeline uses Piper. Silent if `espeak-ng` is not installed (`FileNotFoundError` is caught and ignored).
