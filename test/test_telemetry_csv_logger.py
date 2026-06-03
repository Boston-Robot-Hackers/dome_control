"""Tests for telemetry CSV logging (feature F17, task TF17-T08)."""
import csv
import os
import tempfile
from datetime import datetime
from types import SimpleNamespace

from dome_control.telemetry.csv_logger import (
    FIELDS,
    HEADER,
    TelemetryCsvLogger,
    filename_for,
    row_for,
)


def make_msg(**over):
    base = {f: 0.0 for f in FIELDS}
    base["oak_usb_speed"] = 3
    base["ups_percent"] = 73.8
    base.update(over)
    return SimpleNamespace(**base)


def test_filename_is_ddmmyy():
    assert filename_for(datetime(2025, 12, 31, 14, 30)) == "telemetry311225.csv"


def test_row_starts_with_timestamp_then_fields():
    now = datetime(2025, 12, 31, 14, 30, 5)
    row = row_for(make_msg(ups_percent=80.0), now)
    assert row[0] == "2025-12-31T14:30:05"
    assert len(row) == len(HEADER)
    assert row[HEADER.index("ups_percent")] == 80.0


def test_writes_header_once_and_appends():
    with tempfile.TemporaryDirectory() as tmp:
        logger = TelemetryCsvLogger(base_dir=tmp, max_files=25)
        now = datetime(2025, 12, 31, 14, 30, 5)
        logger.log(make_msg(ups_percent=70.0), now)
        logger.log(make_msg(ups_percent=71.0), now)

        path = os.path.join(tmp, "telemetry311225.csv")
        with open(path) as fh:
            rows = list(csv.reader(fh))
        assert rows[0] == list(HEADER)        # header once
        assert len(rows) == 3                 # header + 2 data rows
        assert rows[1][HEADER.index("ups_percent")] == "70.0"


def test_new_day_new_file():
    with tempfile.TemporaryDirectory() as tmp:
        logger = TelemetryCsvLogger(base_dir=tmp, max_files=25)
        logger.log(make_msg(), datetime(2025, 12, 31, 23, 59))
        logger.log(make_msg(), datetime(2026, 1, 1, 0, 1))
        names = sorted(os.listdir(tmp))
        assert names == ["telemetry010126.csv", "telemetry311225.csv"]


def test_prunes_to_max_files_by_mtime():
    with tempfile.TemporaryDirectory() as tmp:
        logger = TelemetryCsvLogger(base_dir=tmp, max_files=3)
        # Five different days -> five files; create with increasing mtime.
        days = [datetime(2025, 12, d, 12, 0) for d in (1, 2, 3, 4, 5)]
        for i, day in enumerate(days):
            logger.log(make_msg(), day)
            # Force mtime order so 'oldest' is deterministic.
            path = os.path.join(tmp, filename_for(day))
            os.utime(path, (1000 + i, 1000 + i))
            logger.prune()
        remaining = sorted(os.listdir(tmp))
        # Only the 3 newest (days 3,4,5) survive.
        assert remaining == [
            "telemetry031225.csv", "telemetry041225.csv", "telemetry051225.csv",
        ]
