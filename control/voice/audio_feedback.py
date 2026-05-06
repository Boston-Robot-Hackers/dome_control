#!/usr/bin/env python3
"""Simple audio feedback tones and speech for voice state transitions."""

import math
import os
import ctypes

_pa = None


def _get_pa():
    global _pa
    if _pa is None:
        # Suppress ALSA error spam during device enumeration
        try:
            asound = ctypes.cdll.LoadLibrary("libasound.so.2")
            asound.snd_lib_error_set_handler(None)
        except Exception:
            pass
        import pyaudio
        _pa = pyaudio.PyAudio()
    return _pa


def beep(frequency: int = 880, duration: float = 0.15, device_index: int = 0) -> None:
    """Play a short sine-wave tone through the output device."""
    try:
        import numpy as np
    except ImportError:
        return

    pa = _get_pa()
    sample_rate = 16000
    n = int(sample_rate * duration)
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * math.pi * frequency * t) * 32767 * 0.05).astype(np.int16)

    stream = pa.open(
        format=pa.get_format_from_width(2), channels=1, rate=sample_rate,
        output=True, output_device_index=device_index,
    )
    try:
        stream.write(samples.tobytes())
    finally:
        stream.stop_stream()
        stream.close()
