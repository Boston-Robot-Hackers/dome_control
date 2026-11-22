# Notes

Semi-permanent project notes go here: architecture decisions, calibration details,
integration constraints, and research that should survive across sessions.

## What is built

### CLI and dispatch

- CLI has REPL and non-interactive modes
  (`SimpleCLI` → `CommandDispatcher.dispatch_text`).
- **Two routing paths:**
  - *Behavior path:* behavior commands (`scene describe`, `scene objects`,
    `intent stop`, …) publish JSON to `/intent` via `IntentPublisher`. Query
    intents wait up to 5 s for a reply on `/announcement` and print it.
  - *Direct path:* every other command calls `RobotController` synchronously.
- `RobotController` orchestrates the ROS2 API wrappers: movement,
  calibration, process, intent publishing, survey.
- Launch management through configured templates; map save/list/serialize.
- `robot subsystems` (F22) reports running/not-running for `gendrv`/`nav`/
  `semantic`/`control`/`mission`/`vision` via a per-subsystem `ps aux`
  keyword grep (`ProcessApi.get_subsystem_status()`). It also shows
  `mission`'s live FSM state from `/mission/state`
  (`ProcessApi.get_mission_state()`, ~1 s deadline, `"unknown"` on timeout).

### Behaviors and `/intent`

- `BehaviorManagerNode` subscribes to `/intent` and `/oak/detections` and
  routes to domain handlers. It caches the latest `Detection2DArray` in
  `latest_detections` for `PerceptionBehavior`.
- `MotionBehavior`: `stop`, `drive_square`, `turn_right`, `turn_left`,
  `get_status`.
- `PerceptionBehavior`: `describe_scene` (async `/describe_scene` Trigger
  call to `SemanticMapNode`) and `list_objects` (cached detections). If the
  service is not ready it logs a warning and calls anyway; failures are
  logged only, never announced (see `process/01-literate/14-*`).
- `IntentParser`: pure-Python JSON → Intent parser.
- `describe_scene_stub` node for smoke testing without vision hardware.
- **`/intent` ownership is split (F19)**, each name handled by exactly one
  package:
  - `dome_control`: `stop`, `drive_square`, `turn_right`, `turn_left`,
    `get_status`, `describe_scene`, `count_objects`.
  - `dome_mission` (`mission_node`, driving Nav2 + dome_nav's
    `ExploreArea`): `exploration_start`, `exploration_stop`,
    `navigation_go`, `navigation_cancel`.
- **No coordinated stop:** `stop` is a pure motor halt with no knowledge of
  `dome_mission`'s FSM. Cancelling a mission goal is the separate
  `mission.go.stop` / `mission.explore.stop` (F21 renamed `nav` to
  `mission`).
- `dome_mission` publishes its FSM state (`IDLE`/`EXPLORING`/…) on
  `/mission/state` (`std_msgs/String`, transient-local) at startup and on
  every transition (F22 T02).

### Survey

- `SpinSurvey` + `SpinSurveyNode`: the 360° spin, moved from `dome_vision`.
  The node is triggered by the `/survey/start` Trigger service.
- `survey start` CLI → `SurveyApi` → `/survey/start`.

### Launch files

- Each package owns its own robot launch:
  - `dome_control/launch/robot.launch.py`: behavior_manager, telemetry,
    spin_survey; follows the DOME launch convention, spin_survey params in
    `config/spin_survey.yaml`. No `remote.launch.py` (deleted in dome2 F05).
  - `dome_voice/launch/robot.launch.py`: voice_input (Seeed board assumed).
  - `dome_vision_ros/launch/robot.launch.py`: OAK camera + semantic_map +
    optional spin_survey.
- Battery telemetry starts with hardware bringup: `dome_telemetry`'s launch
  is included from dome2's `gendrv.launch.py`.

### Voice (sibling package `dome_voice`)

- `voice_input_node.py` and `audio_feedback.py` (aplay beep, 20 % amplitude)
  live there.
- 8 single-word commands: stop, right, left, explore, describe, objects,
  status, help.
- Wake word "alexa": threshold 0.7, wake_hits 3, cooldown 1.5 s.

### Battery SoC (`dome_telemetry/ups_status.py`)

- `SocEstimator` replaced linear `battery_percent`. It tracks session-peak
  voltage as a `v_full` proxy, because batteries keep rising for ~1–2 h
  after charge.
- `v_empty=9.0V`, `v_full_initial=12.18V`, `r_int=0.0Ω` (wired, disabled).
- INA219 convention: positive current = discharging, so sag correction is
  `voltage + I*R`.

## Config location

- Control config lives at `~/.dome/config/control.yaml` (moved from
  `~/.control/config.yaml` on 2026-08-04). The path is fixed; the
  `CONTROL_CONFIG` env var no longer works.
- A script still pointing at the old path or env var **silently picks up
  nothing** — check that the file exists.

## Lint baseline

- `ruff check` and `ruff format --check` pass (ruff 0.17 in `~/.local/bin`,
  config in `ruff.toml`, same as dome_mission).
- Only two `except Exception` remain, both real boundaries with
  `noqa: BLE001`: `CommandDispatcher.execute_command` and the
  `/describe_scene` future callback.
- `ruff format` also formats Python blocks inside `.md` files.

## Quick commands

```bash
# Tests (workspace must be sourced)
source ~/ros2_ws/install/setup.bash
python3 -m pytest test/ -v

# CLI
ros2 run dome_control run

# On robot — three separate terminals
bl dome_control robot.launch.py
bl dome_voice robot.launch.py
bl dome_vision_ros robot.launch.py

# Battery telemetry (starts with hardware driver bringup)
bl dome2 gendrv.launch.py
ros2 topic echo /telemetry/battery

# Stub mode (no OAK hardware)
bl dome_control robot.launch.py
ros2 run dome_control describe_scene_stub
```

## Telemetry (F17)

- `/telemetry` carries **one flat typed** `dome_control/msg/Telemetry` (all metrics
  are flat named scalars) so Foxglove plots `/telemetry.<field>` directly — no JSON.
  This diverges from `dome_vision`'s F62, which uses one typed message per source.
- The `TelemetryNode` collector lives in `dome_control` and owns no hardware.
  **UPS comes by subscribing** to `/telemetry/battery`
  (`dome_telemetry_msgs/BatteryStats`, from the sibling `dome_telemetry`
  package since F20); **OAK by subscribing** to `/telemetry/oak`
  (`dome_telemetry_msgs/OakStats`) published by `dome_vision_ros`.
- **Why subscribe for OAK** (resolves the earlier USB-ownership conflict): an OAK is
  one USB device with one owner, and the vision stack owns it. Subscribing lets
  telemetry and vision run at the same time, and gives us `fps` + inference timings
  (`pipeline_get_ms`/`tracker_ms`/`iter_ms`) that a direct device read could not.
  UPS moved out the same way in F20: `dome_telemetry` owns the INA219, so
  `dome_control` no longer imports `smbus` or opens I2C.
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
