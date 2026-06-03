# Notes

Semi-permanent project notes go here: architecture decisions, calibration details,
integration constraints, and research that should survive across sessions.

## Telemetry (F17)

- `/telemetry` carries **one flat typed** `dome_control/msg/Telemetry` (all metrics
  are flat named scalars) so Foxglove plots `/telemetry.<field>` directly — no JSON.
  This diverges from `dome_vision`'s F62, which uses one typed message per source.
- The `TelemetryNode` collector lives in `dome_control`. **UPS is read directly**
  (INA219 over I2C); **OAK is read by subscribing** to `/telemetry/oak`
  (`dome_telemetry_msgs/OakStats`) published by `dome_vision_ros`.
- **Why subscribe for OAK** (resolves the earlier USB-ownership conflict): an OAK is
  one USB device with one owner, and the vision stack owns it. Subscribing lets
  telemetry and vision run at the same time, and gives us `fps` + inference timings
  (`pipeline_get_ms`/`tracker_ms`/`iter_ms`) that a direct device read could not.
  UPS stays direct because nothing else owns the INA219.
- Dependency: `dome_control` → `dome_telemetry_msgs` (msg-only pkg). Legal —
  `dome_control` already depends on `dome_vision_ros`, and the msg pkg doesn't
  depend back. The "no dependency on `dome_vision`" rule is about the app package,
  not the shared message package.
- **Host (Pi)** stats are read directly from `/sys` + `/proc`
  (`dome_control/telemetry/host_stats.py`, no extra deps): `pi_cpu_temp_c`
  (thermal_zone0), `pi_cpu_pct` (delta of two `/proc/stat` samples across ticks →
  first tick is 0), `pi_mem_used_mb` (MemTotal−MemAvailable). Missing files → 0, so
  non-Pi hosts keep publishing.
- Host uptime (`pi_uptime_s`) from `/proc/uptime` (seconds since boot).
- **CSV logging**: a second timer (`log_interval_s`, default 10 s) appends the latest
  published message to `~/.dome/telemetry/telemetryDDMMYY.csv`. A new calendar day
  rolls to a new filename automatically. Keep at most `max_log_files` (default 25)
  files, pruning oldest **by mtime** — DDMMYY names don't sort chronologically.
  Logger records `self._latest_msg` (no re-read of hardware). Config keys live in
  `config/telemetry.yaml`.
- Publish rate from `config/telemetry.yaml` (`publish_rate_hz`, default 1).
- OAK fields stay 0 until the first `/telemetry/oak` message arrives (vision down → 0).
