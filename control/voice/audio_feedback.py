#!/usr/bin/env python3
"""Simple audio feedback tones and speech for voice state transitions."""

import ctypes
import math

_pa = None

# No-op error handlers — must be kept alive (not GC'd) for the lifetime of the process
_ALSA_ERROR_HANDLER = None
_JACK_ERROR_HANDLER = None


def _suppress_audio_noise() -> None:
    global _ALSA_ERROR_HANDLER, _JACK_ERROR_HANDLER

    try:
        asound = ctypes.cdll.LoadLibrary("libasound.so.2")
        _ALSA_ERROR_HANDLER = ctypes.CFUNCTYPE(
            None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
        )(lambda *_: None)
        asound.snd_lib_error_set_handler(_ALSA_ERROR_HANDLER)
    except Exception:
        pass

    try:
        jack = ctypes.cdll.LoadLibrary("libjack.so.0")
        _JACK_ERROR_HANDLER = ctypes.CFUNCTYPE(None, ctypes.c_char_p)(lambda *_: None)
        jack.jack_set_error_function(_JACK_ERROR_HANDLER)
        jack.jack_set_info_function(_JACK_ERROR_HANDLER)
    except Exception:
        pass


def _get_pa():
    global _pa
    if _pa is None:
        _suppress_audio_noise()
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
