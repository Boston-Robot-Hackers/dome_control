# Feature description for feature F17

## F17 — combined robot telemetry topic for Foxglove graphing
**Priority**: Medium
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Note:** Unit suite green (193 tests). Verified live on hardware — `/telemetry`
echo showed populated UPS + OAK + host fields with vision and telemetry running
together (no USB conflict).

**Description**: Publish a single combined runtime-telemetry message on one ROS2
topic (`/telemetry`) so values can be plotted over time in a Foxglove Plot panel.
Unlike `dome_vision`'s F62 (one typed message per source), this feature uses **one
flat, typed message spanning all sources** — UPS power, OAK device, and host/other
metrics — collected and published by a single collector node living in
`dome_control`.

Design decisions (agreed with user):
- **One flat, typed message.** `dome_control/msg/Telemetry.msg` carries a
  `std_msgs/Header` plus flat named scalar fields (`ups_*`, `oak_*`, `pi_*`), each a
  typed numeric (mostly `float32`). Foxglove plots `/telemetry.<field>` directly —
  no JSON, no array indexing, no string parsing. One header = one atomic snapshot
  per tick.
- **Lives in `dome_control`.** Message added to the existing `dome_control/msg/`
  (already an `ament_cmake` + `rosidl` package building `Announcement.msg`). No new
  message package. Collector node and config also in `dome_control`. `dome_vision`
  does not depend on `dome_control`; dependency direction stays legal.
- **Single collector node, mixed sources.** `telemetry_node.py` reads the UPS via
  the INA219 driver (`ups_status.py`) directly over I2C, and gets OAK stats by
  **subscribing** to `/telemetry/oak` (`dome_telemetry_msgs/OakStats`, published by
  `dome_vision_ros`). Host (`pi_*`) stats are read directly from `/sys` + `/proc`.
- **OAK by subscription so telemetry + vision coexist.** An OAK is one USB device
  with one owner, and the vision stack owns it; opening our own `dai.Device` would
  conflict whenever vision runs — which is exactly when telemetry is wanted.
  Subscribing avoids the conflict and additionally yields `fps` and inference
  timings (`pipeline_get_ms`/`tracker_ms`/`iter_ms`) a direct read cannot. UPS stays
  direct because nothing else owns the INA219. Dependency `dome_control` →
  `dome_telemetry_msgs` (msg-only) is legal; it does not depend back.
- **YAML config drives the publish rate.** `config/telemetry.yaml` declares at least
  `publish_rate_hz`, **default `1`**. Node reads it at startup and publishes on a
  timer at that rate.

Scope of THIS feature:
1. `dome_control/msg/Telemetry.msg` — flat typed fields (UPS, OAK incl. fps + perf
   timings, host `pi_*`), header, wired into `CMakeLists.txt`
   `rosidl_generate_interfaces` with `std_msgs` dependency.
2. `dome_control/dome_control/nodes/telemetry_node.py` — collector node: reads UPS
   (INA219) + host (`/proc`,`/sys`), subscribes `/telemetry/oak`, merges, publishes
   `/telemetry` on a timer.
3. `dome_control/config/telemetry.yaml` — `publish_rate_hz: 1`, `log_interval_s: 10`,
   `max_log_files: 25`. Node loads it.
4. `dome_control/telemetry/host_stats.py` — pure `/proc`+`/sys` host reader
   (incl. `pi_uptime_s` from `/proc/uptime`).
5. `dome_control/telemetry/csv_logger.py` — append latest message every
   `log_interval_s` to `~/.dome/telemetry/telemetryDDMMYY.csv`; new file per day;
   keep `max_log_files` newest (prune oldest by mtime).
6. Launch wiring + `scripts/` entry point so the node runs in the stack.

Out of scope:
- Removing/altering `dome_vision`'s F62 `/telemetry/oak` work.

## How to Demo
**Setup**: Robot powered via the INA219 UPS, OAK-D on USB, ROS2 stack built and
sourced, Foxglove connected.

**Steps**:
1. Build: `colcon build --packages-select dome_control`, then
   `source install/setup.bash`.
2. Run the collector node (via launch or `ros2 run`).
3. In Foxglove, open a Plot panel and add series `/telemetry.ups_percent` and
   `/telemetry.oak_chip_temp_c`.
4. After ~10 s, check `~/.dome/telemetry/telemetryDDMMYY.csv` exists with a header
   row and growing data rows.

**Expected output**: Live line graphs updating at 1 Hz; values are numeric
(ups_percent ~0–100, oak temp ~50–65 °C) with no JSON or string parsing. The CSV
gains one row every `log_interval_s` (default 10 s); a new day starts a new file and
no more than `max_log_files` (default 25) files are retained.
