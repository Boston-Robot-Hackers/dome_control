---
version: "1.0"
generated: "2026-11-22"
---

# host_stats — Raspberry Pi health from `/proc` and `/sys`

`telemetry/host_stats.py` reads four host metrics for the telemetry node:
CPU temperature, CPU usage, memory used and uptime. It uses only the
kernel's pseudo-files, with no `psutil` or other dependency. Parsing is
split into small pure functions that take text, so tests feed them strings
instead of real files.

## Four sources, four parsers

| Metric | File | Parser |
|---|---|---|
| `cpu_temp_c` | `/sys/class/thermal/thermal_zone0/temp` | milli-°C text → °C |
| `cpu_pct` | `/proc/stat` | delta of two samples |
| `mem_used_mb` | `/proc/meminfo` | (MemTotal − MemAvailable) / 1024 |
| `uptime_s` | `/proc/uptime` | first field |

## CPU usage is a rate, so it needs memory

`/proc/stat`'s first line holds cumulative *jiffies* (scheduler ticks)
spent in each CPU state since boot. A usage percentage only makes sense
**between two samples**:

```python
def parse_cpu_totals(stat_text):
    for line in stat_text.splitlines():
        if line.startswith("cpu "):
            parts = [int(x) for x in line.split()[1:]]
            idle = parts[3] + (parts[4] if len(parts) > 4 else 0)  # idle + iowait
            return idle, sum(parts)

def cpu_pct_from_deltas(prev, cur):
    delta_total = cur_total - prev_total
    delta_idle = cur_idle - prev_idle
    if delta_total <= 0:
        return 0.0
    return max(0.0, min(100.0, (delta_total - delta_idle) / delta_total * 100.0))
```

This is the classic `top` calculation: busy = Δtotal − Δidle. Counting
`iowait` as idle matches `top`'s convention. `HostStatsReader` keeps the
previous sample across ticks, so the first reading is always 0.

One subtlety: `/proc/stat`'s `guest` and `guest_nice` columns are already
included in `user` and `nice`, so summing all fields double-counts guest
time. On a Pi without VMs those columns are 0, so it doesn't matter here.

## "MemAvailable", not "MemFree"

Used memory is `MemTotal − MemAvailable`. `MemAvailable` counts reclaimable
page cache as available, which matches how much the system can actually
still use. `MemFree` would make a healthy Pi look nearly full.

## Fail-soft to zero

```python
def read_text_file(path):
    try:
        with open(path) as fh:
            return fh.read()
    except OSError:
        return None
```

Any unreadable file yields 0 for its field, so telemetry keeps flowing on
a laptop without a thermal zone.

## Observations

1. **Zero is ambiguous.** A plot can't tell "0 % CPU" from "couldn't
   read", and the first tick always reports 0 %. Publish `NaN` for unknown
   values (Foxglove draws a gap) instead of 0.
2. **Parsers raise on malformed input** (for example `int(raw.strip())` on
   a non-numeric temp file), while unreadable files fail soft. Pick one
   policy. Malformed kernel files are rare enough that raising is
   reasonable.
3. **Thermal zone 0 is hard-coded.** On a Pi 5 that is the CPU. Other
   boards may number zones differently, so the path is worth having in
   `telemetry.yaml` if the stack ever runs elsewhere.
4. **The `.py` file has no shebang**, against the style guide's MUST
   (`telemetry/config.py` and `csv_logger.py` too). ruff's `EXE001` is
   ignored, so the check doesn't catch it.
