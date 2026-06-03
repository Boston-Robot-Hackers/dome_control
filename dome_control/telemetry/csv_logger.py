# csv_logger — append telemetry rows to a daily, count-capped CSV file
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Append telemetry rows to a daily CSV file (feature F17).

One file per day named ``telemetryDDMMYY.csv`` under ``~/.dome/telemetry/``. A new
day automatically writes to a new filename. At most ``max_files`` files are kept;
when a new day's file is created, the oldest files (by modification time) are pruned.

Pure-ish: the directory and "now" are injectable so the logic unit-tests against a
temp dir without waiting for real time to pass. ``DDMMYY`` does not sort
chronologically, so pruning is by file mtime, not by name.
"""
import csv
import glob
import os

DEFAULT_DIR = "~/.dome/telemetry"

# Column order = the flat Telemetry fields, with a leading wall-clock timestamp.
FIELDS = (
    "ups_bus_voltage_v", "ups_current_a", "ups_power_w", "ups_percent",
    "oak_fps", "oak_chip_temp_c", "oak_usb_speed", "oak_cmx_mem_used_mb",
    "oak_ddr_mem_used_mb", "oak_leon_css_cpu_pct", "oak_leon_mss_cpu_pct",
    "oak_pipeline_get_ms", "oak_tracker_ms", "oak_iter_ms",
    "pi_cpu_temp_c", "pi_cpu_pct", "pi_mem_used_mb", "pi_uptime_s",
)
HEADER = ("timestamp",) + FIELDS


def filename_for(now):
    """Daily filename for the given datetime: telemetryDDMMYY.csv."""
    return f"telemetry{now:%d%m%y}.csv"


def row_for(msg, now):
    """Build a CSV row (list) from a Telemetry msg and a datetime."""
    return [now.isoformat(timespec="seconds")] + [getattr(msg, f) for f in FIELDS]


class TelemetryCsvLogger:
    """Appends Telemetry rows to the current day's CSV, pruning old files."""

    def __init__(self, base_dir=DEFAULT_DIR, max_files=25):
        self.dir = os.path.expanduser(base_dir)
        self.max_files = max_files

    def log(self, msg, now):
        """Append one row for `msg` stamped at datetime `now`."""
        os.makedirs(self.dir, exist_ok=True)
        path = os.path.join(self.dir, filename_for(now))
        is_new = not os.path.exists(path)
        with open(path, "a", newline="") as fh:
            writer = csv.writer(fh)
            if is_new:
                writer.writerow(HEADER)
            writer.writerow(row_for(msg, now))
        if is_new:
            self.prune()

    def prune(self):
        """Keep at most max_files telemetry*.csv, deleting oldest by mtime."""
        files = glob.glob(os.path.join(self.dir, "telemetry*.csv"))
        if len(files) <= self.max_files:
            return
        files.sort(key=os.path.getmtime)  # oldest first
        for stale in files[: len(files) - self.max_files]:
            try:
                os.remove(stale)
            except OSError:
                pass
