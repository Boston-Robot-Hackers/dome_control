---
version: "1.0"
generated: "2026-06-03"
---

# TelemetryNode: Combined Robot Telemetry Publisher

`TelemetryNode` is a regular ROS2 `Node` (feature F17) that collects runtime
statistics from multiple hardware sources and publishes them as one flat,
Foxglove-plottable message on `/telemetry`.

## Design Decision: One Flat Typed Message

Unlike `dome_vision`'s per-source telemetry (F62), this node publishes a **single**
`dome_control/msg/Telemetry` carrying every metric as a flat named scalar field
(`ups_*`, `oak_*`, `pi_*`). A Foxglove Plot series is then just a message path —
`/telemetry.ups_percent` — resolving to a number, with no JSON, no array indexing,
no string parsing. One `std_msgs/Header` means one atomic snapshot per tick.

## Design Decision: UPS Direct, OAK by Subscription

The node mixes two source strategies so it can run **alongside the vision stack**:

- **UPS** — opens an `INA219` (`ups_status.py`) over I2C and calls `read_ups_stats`.
  Nothing else owns the INA219, so a direct read is safe.
- **OAK** — **subscribes** to `/telemetry/oak` (`dome_telemetry_msgs/OakStats`),
  published by the vision node (`dome_vision_ros`), and caches the latest message.

An OAK is a single USB device with one owner, and the vision stack owns it. Opening
our own `dai.Device` would conflict whenever vision is running — which is exactly
when you want telemetry. Subscribing sidesteps that entirely and, as a bonus, gives
us `fps` and the inference-loop timings (`pipeline_get_ms`, `tracker_ms`, `iter_ms`)
that a directly-opened device cannot provide.

- **Host (Pi)** — `HostStatsReader` reads `/sys` and `/proc` each tick (CPU temp,
  CPU usage as a delta between ticks, memory used). Pure files, no extra deps.

All sources **fail soft**: if the INA219 cannot be opened, UPS fields stay zero; if
no `OakStats` has arrived yet (vision down), OAK fields stay zero; if `/proc`/`/sys`
files are missing (non-Pi host), host fields stay zero. Either way the node keeps
publishing `/telemetry`.

## Topics

| Direction | Topic | Type |
|-----------|-------|------|
| Publish | `/telemetry` | `dome_control/msg/Telemetry` (every tick at `publish_rate_hz`) |
| Subscribe | `/telemetry/oak` | `dome_telemetry_msgs/OakStats` (from `dome_vision_ros`) |

## Message Fields

`dome_control/msg/Telemetry` — every field is a plain number, plottable as
`/telemetry.<field>`. Canonical per-field docs are the inline comments in
`msg/Telemetry.msg` (`ros2 interface show dome_control/msg/Telemetry`).

| Field | Unit | Source | Notes |
|-------|------|--------|-------|
| `header.stamp` | — | node | publish time |
| `ups_bus_voltage_v` | V | INA219 | load-side bus voltage |
| `ups_current_a` | A | INA219 | negative = charging, positive = discharging |
| `ups_power_w` | W | INA219 | |
| `ups_percent` | % 0–100 | INA219 | 3S-LiPo linear 9 V=0 %, 12.6 V=100 %, ±20 % |
| `oak_fps` | fps | /telemetry/oak | over the reporting window |
| `oak_chip_temp_c` | °C | /telemetry/oak | device average chip temp |
| `oak_usb_speed` | enum | /telemetry/oak | 2=USB2, 3=USB3, 0=unknown |
| `oak_cmx_mem_used_mb` | MB | /telemetry/oak | CMX memory in use |
| `oak_ddr_mem_used_mb` | MB | /telemetry/oak | DDR memory in use |
| `oak_leon_css_cpu_pct` | % | /telemetry/oak | Leon CSS core CPU |
| `oak_leon_mss_cpu_pct` | % | /telemetry/oak | Leon MSS core CPU |
| `oak_pipeline_get_ms` | ms | /telemetry/oak | mean blocking wait on queue get() |
| `oak_tracker_ms` | ms | /telemetry/oak | mean tracker update time |
| `oak_iter_ms` | ms | /telemetry/oak | mean full inference-loop iteration |
| `pi_cpu_temp_c` | °C | /sys thermal_zone0 | host CPU temperature |
| `pi_cpu_pct` | % | /proc/stat | host CPU usage since previous tick |
| `pi_mem_used_mb` | MB | /proc/meminfo | MemTotal − MemAvailable |
| `pi_uptime_s` | s | /proc/uptime | host uptime since boot |

## Configuration

`config/telemetry.yaml` declares three keys, loaded via `load_telemetry_config`
(overridable with the `config_path` ROS parameter); each falls back to its default
on a missing/invalid value:

| Key | Default | Meaning |
|-----|---------|---------|
| `publish_rate_hz` | 1 | `/telemetry` publishes per second |
| `log_interval_s` | 10 | seconds between CSV log rows |
| `max_log_files` | 25 | daily CSV files kept (oldest pruned) |

## CSV Logging

A second timer fires every `log_interval_s` (default 10 s) and appends the latest
published message as a row to a daily CSV via `TelemetryCsvLogger`:

- **Path**: `~/.dome/telemetry/telemetryDDMMYY.csv`. A new calendar day writes to a
  new filename automatically (the timer just computes today's name each tick).
- **Header**: written once when a file is first created — `timestamp` followed by
  every `Telemetry` field in order (see `csv_logger.FIELDS`).
- **Retention**: at most `max_log_files` files are kept. When a new day's file is
  created, older files are pruned **by modification time** (the `DDMMYY` name does
  not sort chronologically, so name-sort would be wrong).
- **Fail-soft**: a write/`OSError` is logged as a warning; publishing continues.

The logger only runs off `self._latest_msg` (the last thing published), so logging
never re-reads hardware — it records exactly what went out on the topic.

## The Mapping Function

`build_message(ups, oak, host, clock)` is pure and unit-tested: it stamps the header
and copies whichever sources are present — `ups` (a `UpsStats`), `oak` (the latest
`OakStats` message), and `host` (a `HostStats`); any may be `None`.

## Flow

```
__init__
    ├── load telemetry.yaml → publish_rate_hz
    ├── _UpsReader(open INA219)            ─ fail soft → ups fields 0
    ├── HostStatsReader()                  ─ fail soft → pi fields 0
    ├── TelemetryCsvLogger(max_files)
    ├── subscribe /telemetry/oak → self.latest_oak (None until first msg)
    ├── create_timer(1/rate, tick)
    └── create_timer(log_interval_s, log_tick)
            │
            ▼ tick()                         ▼ log_tick()  (every log_interval_s)
        ups  = self.ups.read()           if self.latest_msg:
        oak  = self.latest_oak               csv.log(self.latest_msg, now())
        host = self.host.read()
        self.latest_msg = build_message(ups, oak, host, clock)
        publish self.latest_msg
```
