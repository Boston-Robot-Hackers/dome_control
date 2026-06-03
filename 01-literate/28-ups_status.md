---
version: "1.0"
generated: "2026-06-03"
---

# ups_status: INA219 UPS Driver and Stats Reader

`ups_status.py` is the low-level driver for the robot's UPS, an **INA219** current/
power monitor read over I2C. It provides both a raw register driver and a clean
data-returning API used by `TelemetryNode` (feature F17).

## The INA219 Driver

The `INA219` class is a thin register-level driver. It assumes a **0.1 Ω shunt**
resistor and is calibrated for the 32V / 2A range (`set_calibration_32V_2A`), giving
a current LSB of 100 µA and power LSB of 2 mW. The chip exposes exactly six
registers (config, shunt voltage, bus voltage, power, current, calibration); the
driver maps each. Reads recalibrate first because the chip can reset its calibration
on certain bus events.

| Reader | Returns | Notes |
|--------|---------|-------|
| `getBusVoltage_V` | load-side voltage (V) | first read discarded, then `>>3 * 0.004` |
| `getShuntVoltage_mV` | shunt drop (mV) | signed |
| `getCurrent_mA` | current (mA) | **negative = charging, positive = discharging** |
| `getPower_W` | power (W) | |

## Design Decision: Return Data, Never Print

The original module only printed in a `while True` loop. F17 added a clean,
testable API that returns data and is decoupled from any I/O loop:

- `UpsStats` — a dataclass snapshot: `bus_voltage_v`, `current_a`, `power_w`,
  `percent`.
- `read_ups_stats(ina)` — reads an existing `INA219` handle, converts mA → A, and
  computes `percent`. It opens no device and prints nothing, so the ROS node maps
  it straight onto a message and tests drive it with a mock INA219.

The legacy `__main__` print loop is preserved for manual hardware checks, but now
drives off `read_ups_stats` so the demo and the node share one code path.

## Battery Percent

`battery_percent(bus_voltage_v)` is a **linear** 3S-LiPo estimate: 9.0 V = 0 %,
12.6 V = 100 % (3.0–4.2 V per cell), clamped to 0–100.

> Accuracy ±20 %. The LiPo discharge curve is nonlinear and voltage sags under load.
> A different chemistry (lead-acid, LiFePO4) gives wrong numbers entirely.
