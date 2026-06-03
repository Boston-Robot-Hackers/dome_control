# config — load and validate the telemetry collector node's YAML config
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Config loading for the telemetry collector node (feature F17).

Pure Python, no ROS imports — so it is unit-testable without a running graph.
"""
import os

import yaml

DEFAULT_PUBLISH_RATE_HZ = 1.0
DEFAULT_LOG_INTERVAL_S = 10.0
DEFAULT_MAX_LOG_FILES = 25


def positive_float(raw, key, default):
    """Coerce raw[key] to a positive float, falling back to default."""
    val = raw.get(key, default)
    try:
        val = float(val)
    except (TypeError, ValueError):
        return default
    return val if val > 0 else default


def positive_int(raw, key, default):
    """Coerce raw[key] to a positive int, falling back to default."""
    val = raw.get(key, default)
    try:
        val = int(val)
    except (TypeError, ValueError):
        return default
    return val if val > 0 else default


def load_telemetry_config(path=None):
    """Load telemetry config, returning a dict with safe defaults.

    Always returns ``{"publish_rate_hz": <positive float>,
    "log_interval_s": <positive float>, "max_log_files": <positive int>}``. A
    missing file, missing key, or non-positive value falls back to the default.
    """
    raw = {}
    if path and os.path.exists(os.path.expanduser(path)):
        with open(os.path.expanduser(path)) as fh:
            loaded = yaml.safe_load(fh) or {}
        # Accept either a top-level "telemetry:" block or a flat mapping.
        raw = loaded.get("telemetry", loaded) if isinstance(loaded, dict) else {}

    return {
        "publish_rate_hz": positive_float(
            raw, "publish_rate_hz", DEFAULT_PUBLISH_RATE_HZ
        ),
        "log_interval_s": positive_float(
            raw, "log_interval_s", DEFAULT_LOG_INTERVAL_S
        ),
        "max_log_files": positive_int(
            raw, "max_log_files", DEFAULT_MAX_LOG_FILES
        ),
    }
