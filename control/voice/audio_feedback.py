#!/usr/bin/env python3
"""Simple audio feedback tones and speech for voice state transitions."""

import math
import os

_pa = None


def _get_pa():
    global _pa
    if _pa is None:
        # Suppress ALSA/JACK stderr spam during device enumeration
        devnull = os.open(os.devnull, os.O_WRONLY)
        saved = os.dup(2)
        os.dup2(devnull, 2)
        os.close(devnull)
        try:
            import pyaudio
            _pa = pyaudio.PyAudio()
        finally:
            os.dup2(saved, 2)
            os.close(saved)
    return _pa


def beep(frequency: int = 880, duration: float = 0.15, device_index: int = 0) -> None:
    """Play a short sine-wave tone through the output device."""
    try:
        import numpy as np
    except ImportError:
        return

    try:
        import pyaudio
        pa = _get_pa()
        sample_rate = 16000
        n = int(sample_rate * duration)
        t = np.arange(n) / sample_rate
        samples = (np.sin(2 * math.pi * frequency * t) * 32767 * 0.05).astype(np.int16)

        stream = pa.open(
            format=pyaudio.paInt16, channels=1, rate=sample_rate,
            output=True, output_device_index=device_index,
        )
        try:
            stream.write(samples.tobytes())
        finally:
            stream.stop_stream()
            stream.close()
    except Exception:
        pass
