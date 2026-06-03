"""Tests for telemetry config loader (feature F17, task TF17-T02)."""
import os
import tempfile

from dome_control.telemetry.config import (
    DEFAULT_LOG_INTERVAL_S,
    DEFAULT_MAX_LOG_FILES,
    DEFAULT_PUBLISH_RATE_HZ,
    load_telemetry_config,
)


def write_yaml(tmp, text):
    path = os.path.join(tmp, "telemetry.yaml")
    with open(path, "w") as fh:
        fh.write(text)
    return path


def test_present_key():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_yaml(tmp, "telemetry:\n  publish_rate_hz: 5\n")
        assert load_telemetry_config(path)["publish_rate_hz"] == 5.0


def test_flat_mapping_also_accepted():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_yaml(tmp, "publish_rate_hz: 2\n")
        assert load_telemetry_config(path)["publish_rate_hz"] == 2.0


def test_missing_key_defaults():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_yaml(tmp, "telemetry:\n  something_else: 9\n")
        assert load_telemetry_config(path)["publish_rate_hz"] == DEFAULT_PUBLISH_RATE_HZ


def test_missing_file_defaults():
    cfg = load_telemetry_config("/no/such/file.yaml")
    assert cfg["publish_rate_hz"] == DEFAULT_PUBLISH_RATE_HZ


def test_none_path_defaults():
    assert load_telemetry_config(None)["publish_rate_hz"] == DEFAULT_PUBLISH_RATE_HZ


def test_non_positive_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        for bad in ("0", "-3", "notanumber"):
            path = write_yaml(tmp, f"telemetry:\n  publish_rate_hz: {bad}\n")
            cfg = load_telemetry_config(path)
            assert cfg["publish_rate_hz"] == DEFAULT_PUBLISH_RATE_HZ


def test_default_is_one():
    assert DEFAULT_PUBLISH_RATE_HZ == 1.0


def test_log_keys_present_and_defaulted():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_yaml(tmp, "telemetry:\n  log_interval_s: 30\n  max_log_files: 7\n")
        cfg = load_telemetry_config(path)
        assert cfg["log_interval_s"] == 30.0
        assert cfg["max_log_files"] == 7


def test_log_keys_defaults_when_missing():
    cfg = load_telemetry_config(None)
    assert cfg["log_interval_s"] == DEFAULT_LOG_INTERVAL_S
    assert cfg["max_log_files"] == DEFAULT_MAX_LOG_FILES
    assert DEFAULT_LOG_INTERVAL_S == 10.0
    assert DEFAULT_MAX_LOG_FILES == 25


def test_max_log_files_non_positive_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_yaml(tmp, "telemetry:\n  max_log_files: 0\n")
        assert load_telemetry_config(path)["max_log_files"] == DEFAULT_MAX_LOG_FILES
