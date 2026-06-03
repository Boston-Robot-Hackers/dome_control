# Tasks for Feature F17

Task file name is `TF17-telemetry-stats-topic.md`; `17` matches feature F17.
For each task step, add a test when feasible. If not feasible, note why.

## T01 — define the flat Telemetry message
**Status**: done
**Description**: Add `dome_control/msg/Telemetry.msg` with `std_msgs/Header header`
and flat typed fields:
- UPS: `float32 ups_bus_voltage_v`, `float32 ups_current_a`, `float32 ups_power_w`,
  `float32 ups_percent`
- OAK: `float32 oak_chip_temp_c`, `float32 oak_fps`, `uint8 oak_usb_speed`
  (2=USB2/high, 3=USB3/super, 0=unknown), `float32 oak_cmx_mem_used_mb`,
  `float32 oak_ddr_mem_used_mb`, `float32 oak_leon_css_cpu_pct`,
  `float32 oak_leon_mss_cpu_pct`
- Host (reserved): `float32 pi_cpu_temp_c`, `float32 pi_cpu_pct`,
  `float32 pi_mem_used_mb`
Wire into `CMakeLists.txt`: add `"msg/Telemetry.msg"` to
`rosidl_generate_interfaces` and add `std_msgs` to `DEPENDENCIES` +
`find_package(std_msgs REQUIRED)`. `std_msgs` already a `<depend>` in package.xml.
**Test**: `colcon build --packages-select dome_control` succeeds and
`ros2 interface show dome_control/msg/Telemetry` lists all fields. (Build/interface
check is the meaningful test; no unit test for a message definition.)

## T02 — config loading with publish_rate_hz default 1
**Status**: done
**Description**: Add `dome_control/config/telemetry.yaml` with `publish_rate_hz: 1`.
Add a small pure-Python loader (e.g. `load_telemetry_config(path) -> dict`) that
reads the YAML and returns config with `publish_rate_hz` defaulting to `1` when the
key or file is absent. Install the config dir in `CMakeLists.txt`.
**Test**: unit-test the loader — present key, missing key (→1), missing file (→1),
non-positive value rejected/clamped to a sane default.

## T03 — UPS stats collection (return, never print)
**Status**: done
**Description**: Refactor `ups_status.py` so the INA219 reads are available as a
data-returning call (e.g. `read_ups_stats(ina) -> UpsStats` dataclass with
bus_voltage_v, current_a, power_w, percent) without the `__main__` print loop driving
it. Keep the existing `__main__` demo behavior intact (it may call the new function).
**Test**: unit-test `read_ups_stats` against a mock INA219 whose getters return known
values; assert unit conversions (mA→A, percent clamp 0–100, the 9V/12.6V linear map).

## T04 — OAK stats by subscription (not direct device read)
**Status**: done
**Description**: REVISED — instead of opening the OAK directly (USB conflict with the
vision stack), the node subscribes to `/telemetry/oak`
(`dome_telemetry_msgs/OakStats`, published by `dome_vision_ros`) and caches the
latest message. This lets telemetry and vision run together and yields fps + perf
timings a direct read cannot. Add `dome_telemetry_msgs` as a `<depend>` in
package.xml. (The earlier direct-read `telemetry/oak_stats.py` + its test were
removed.)
**Test**: covered by the T05 mapping test, which feeds an OakStats-shaped object
into `build_message`.

## T05 — collector node publishing /telemetry
**Status**: done
**Description**: Add `dome_control/dome_control/nodes/telemetry_node.py`: an `rclpy`
node that loads `telemetry.yaml`, opens the INA219, subscribes to `/telemetry/oak`,
and on a timer at `publish_rate_hz` merges UPS + the latest OakStats onto `Telemetry`,
stamps the header, and publishes `/telemetry`. UPS fails soft (log once); OAK fields
stay 0 until the first message. Add `scripts/telemetry_node` entry point and install
it in `CMakeLists.txt`.
**Test**: unit-test the `build_message` mapping with a fake UpsStats + OakStats-shaped
object and a fake clock; assert field copy and the None/None fail-soft path. Hardware
reads stay manual.

## T06 — launch wiring + tests run + docs
**Status**: done
**Description**: Add the telemetry node to a launch file (own arg/toggle, default
on or as decided). Run the full test suite. Generate `01-literate/telemetry_node.md`
and `01-literate/ups_status.md`; update `02-doc/current.md` and note the combined
single-topic telemetry pattern in `02-doc/notes.md`.
**Test**: `python3 -m pytest test/ -v` passes; manual Foxglove demo per the feature's
How to Demo.

## T07 — host (Pi) stats collection, fill pi_* fields
**Status**: done
**Description**: Add `dome_control/telemetry/host_stats.py`: pure `/proc` + `/sys`
reader (no extra deps) returning a `HostStats` dataclass — `cpu_temp_c`
(thermal_zone0), `cpu_pct` (delta between two `/proc/stat` samples held across ticks),
`mem_used_mb` (MemTotal−MemAvailable from `/proc/meminfo`). Wire a `HostStatsReader`
into the node and fill `pi_*` in `build_message`. Fail soft: missing files → 0
(non-Pi hosts keep working). Update msg/literate so `pi_*` are no longer "reserved".
**Test**: unit-test the pure parse functions (temp, cpu totals, cpu-pct deltas, mem),
the reader's first-tick-zero-then-delta behavior, and missing-file → 0. Node mapping
covered by the T05 `build_message` test (host arg).

## T08 — CSV logging + host uptime
**Status**: done
**Description**: Add `pi_uptime_s` (host uptime from `/proc/uptime`) to the message
and `HostStats`. Add `dome_control/telemetry/csv_logger.py`
(`TelemetryCsvLogger`): every `log_interval_s` (config, default 10) append the latest
published message as a row to `~/.dome/telemetry/telemetryDDMMYY.csv`. New calendar
day → new file automatically. Header written once per file. Keep at most
`max_log_files` (config, default 25) files, pruning oldest **by mtime** (DDMMYY names
don't sort chronologically). Add `log_interval_s` + `max_log_files` to the config
loader and `telemetry.yaml`. Node gets a second timer at `log_interval_s` and logs
`self._latest_msg`; CSV write errors are warn-logged, publishing continues.
**Test**: unit-test `filename_for` (DDMMYY), `row_for` (timestamp + ordered fields),
header-written-once + append, new-day-new-file, and prune-to-max-by-mtime. Config
test covers the two new keys + defaults. Uptime parse + reader covered in host tests.
