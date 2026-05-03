#!/usr/bin/env python3
"""Simple audio feedback tones and speech for voice state transitions."""

import math
import subprocess


def beep(frequency: int = 880, duration: float = 0.15, device_index: int = 0) -> None:
    """Play a short sine-wave tone through the output device."""
    try:
        import pyaudio
        import numpy as np
    except ImportError:
        return

    sample_rate = 16000
    n = int(sample_rate * duration)
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * math.pi * frequency * t) * 32767 * 0.05).astype(np.int16)

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16, channels=1, rate=sample_rate,
        output=True, output_device_index=device_index,
    )
    try:
        stream.write(samples.tobytes())
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


def speak(text: str, speed: int = 150, amplitude: int = 15) -> None:
    """Speak text using espeak-ng. Silent if espeak-ng not installed."""
    try:
        subprocess.run(
            ["espeak-ng", "-s", str(speed), "-a", str(amplitude), text],
            check=False, capture_output=True,
        )
    except FileNotFoundError:
        pass
