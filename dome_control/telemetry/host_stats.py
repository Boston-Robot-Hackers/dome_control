# host_stats — read host (Raspberry Pi) telemetry from /proc and /sys
# Author: Pito Salas and Claude Code
# Open Source Under MIT license
"""Read host (Raspberry Pi) telemetry from /proc and /sys (feature F17).

Pure Python, no ROS, no extra dependencies. Parsing is split into small pure
functions so they unit-test without touching real files. CPU usage is a delta
between two /proc/stat samples, so a HostStatsReader instance is kept across ticks
to hold the previous sample.
"""
from dataclasses import dataclass

KB_PER_MB = 1024
DEFAULT_TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"
DEFAULT_STAT_PATH = "/proc/stat"
DEFAULT_MEMINFO_PATH = "/proc/meminfo"
DEFAULT_UPTIME_PATH = "/proc/uptime"


@dataclass
class HostStats:
    """One snapshot of host metrics, in plot-friendly units."""
    cpu_temp_c: float    # CPU temperature, Celsius
    cpu_pct: float       # CPU usage since the previous sample, percent
    mem_used_mb: float   # memory in use (MemTotal - MemAvailable), megabytes
    uptime_s: float      # host uptime since boot, seconds


def parse_cpu_temp_c(raw):
    """thermal_zone temp file holds milli-Celsius as text -> Celsius."""
    return int(raw.strip()) / 1000.0


def parse_cpu_totals(stat_text):
    """Aggregate 'cpu ' line of /proc/stat -> (idle_jiffies, total_jiffies).

    idle = idle + iowait. total = sum of all fields. Returns (0, 0) if absent.
    """
    for line in stat_text.splitlines():
        if line.startswith("cpu "):
            parts = [int(x) for x in line.split()[1:]]
            idle = parts[3] + (parts[4] if len(parts) > 4 else 0)  # idle + iowait
            return idle, sum(parts)
    return 0, 0


def cpu_pct_from_deltas(prev, cur):
    """CPU usage percent between two (idle, total) samples.

    Returns 0.0 when there is no prior sample or no elapsed jiffies.
    """
    prev_idle, prev_total = prev
    cur_idle, cur_total = cur
    delta_total = cur_total - prev_total
    delta_idle = cur_idle - prev_idle
    if delta_total <= 0:
        return 0.0
    return max(0.0, min(100.0, (delta_total - delta_idle) / delta_total * 100.0))


def parse_uptime_s(uptime_text):
    """/proc/uptime is '<uptime_seconds> <idle_seconds>' -> uptime seconds."""
    return float(uptime_text.split()[0])


def parse_mem_used_mb(meminfo_text):
    """/proc/meminfo -> used MB = (MemTotal - MemAvailable) in kB, /1024."""
    vals = {}
    for line in meminfo_text.splitlines():
        key, sep, rest = line.partition(":")
        if sep and key in ("MemTotal", "MemAvailable"):
            vals[key] = int(rest.split()[0])  # kB
    if "MemTotal" not in vals or "MemAvailable" not in vals:
        return 0.0
    used_kb = vals["MemTotal"] - vals["MemAvailable"]
    return used_kb / KB_PER_MB


def read_text_file(path):
    """Return file contents, or None if it cannot be read."""
    try:
        with open(path) as fh:
            return fh.read()
    except OSError:
        return None


class HostStatsReader:
    """Reads host stats across ticks, holding the previous CPU sample.

    Paths are injectable for tests. A missing/unreadable file yields 0 for that
    field rather than raising, so telemetry keeps flowing on non-Pi hosts.
    """

    def __init__(
        self,
        temp_path=DEFAULT_TEMP_PATH,
        stat_path=DEFAULT_STAT_PATH,
        meminfo_path=DEFAULT_MEMINFO_PATH,
        uptime_path=DEFAULT_UPTIME_PATH,
        read_text=read_text_file,
    ):
        self.temp_path = temp_path
        self.stat_path = stat_path
        self.meminfo_path = meminfo_path
        self.uptime_path = uptime_path
        self.read_text = read_text
        self.prev_cpu = None

    def read(self):
        temp_raw = self.read_text(self.temp_path)
        cpu_temp_c = parse_cpu_temp_c(temp_raw) if temp_raw else 0.0

        stat_text = self.read_text(self.stat_path)
        cpu_pct = 0.0
        if stat_text:
            cur = parse_cpu_totals(stat_text)
            if self.prev_cpu is not None:
                cpu_pct = cpu_pct_from_deltas(self.prev_cpu, cur)
            self.prev_cpu = cur

        meminfo_text = self.read_text(self.meminfo_path)
        mem_used_mb = parse_mem_used_mb(meminfo_text) if meminfo_text else 0.0

        uptime_text = self.read_text(self.uptime_path)
        uptime_s = parse_uptime_s(uptime_text) if uptime_text else 0.0

        return HostStats(
            cpu_temp_c=cpu_temp_c, cpu_pct=cpu_pct, mem_used_mb=mem_used_mb,
            uptime_s=uptime_s,
        )
