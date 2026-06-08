---
version: "1.1"
generated: "2026-06-08"
---

# ups_status: INA219 UPS Driver and Battery SoC Estimator

`ups_status.py` is the low-level driver for the robot's UPS, an **INA219** current/
power monitor read over I2C. It provides both a raw register driver and a clean
data-returning API used by `TelemetryNode` (feature F17). The battery State of
Charge (SoC) is now estimated via a session-peak voltage model rather than a fixed
linear mapping.

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

- `UpsStats` — a dataclass snapshot: `bus_voltage_v`, `current_a`, `power_w`, `percent`.
- `read_ups_stats(ina, estimator)` — reads an existing `INA219` handle, converts
  mA → A, delegates SoC to the estimator. Opens no device and prints nothing.

The legacy `__main__` print loop is preserved for manual hardware checks; it now
drives off `read_ups_stats` so the demo and the node share one code path.

## Battery SoC: Session-Peak Voltage Model

The old `battery_percent` was a fixed linear map (9.0 V = 0%, 12.6 V = 100%). The
problem: the true 100% voltage varies across charge cycles, and voltage continues to
rise for 1–2 hours after the charger disconnects (surface-charge relaxation). A
hardcoded `v_full` is therefore an unreliable anchor.

`SocEstimator` solves this by tracking the **session-peak voltage** as a running proxy
for full charge:

```python
class SocEstimator:
    def estimate(self, voltage: float, current: float = 0.0) -> float:
        self.v_full = max(self.v_full, voltage)
        v_corrected = voltage + current * self.r_int
        soc = (v_corrected - self.v_empty) / (self.v_full - self.v_empty) * 100
        return max(0.0, min(100.0, round(soc, 1)))
```

Key parameters and their defaults:

| Parameter | Default | Source |
|-----------|---------|--------|
| `v_empty` | 9.0 V | observed in telemetry when `ups_percent` hit 0 |
| `v_full_initial` | 12.18 V | peak from telemetry070626.csv |
| `r_int` | 0.0 Ω | wired, disabled; set >0 to correct for load sag |

### Sign Convention for R_INT

The INA219 in this codebase returns **positive current when discharging**. Under
discharge, the measured bus voltage sags below the true open-circuit voltage by
`I × R_int`. To recover the open-circuit voltage estimate we *add* the drop back:

```
v_corrected = voltage + current * r_int
```

This is the opposite sign from algorithms written assuming "negative = discharging".
The `r_int=0.0` default makes the distinction moot until hardware measurements
justify tuning it.

### Ownership and Lifecycle

`TelemetryNode` creates one `SocEstimator` inside `UpsReader.__init__`. It persists
across every read tick, accumulating the session peak. No state is shared between
nodes or test runs.

```
UpsReader.__init__
  └─ self.estimator = SocEstimator()

UpsReader.read()
  └─ read_ups_stats(self.ina, self.estimator)
       └─ estimator.estimate(bus_v, current_a)
            └─ updates self.v_full, returns SoC
```

## Observations and Possible Improvements

- **Non-linear curve**: Lead-acid and LiFePO4 discharge curves are strongly
  nonlinear. A lookup table (voltage → SoC) per chemistry would be more accurate
  than a linear model once the battery chemistry is confirmed.
- **R_INT calibration**: Internal resistance could be auto-estimated from paired
  open-circuit and loaded voltage readings. Currently it requires manual tuning.
- **Session-peak drift**: If the robot is never fully charged during a session,
  `v_full` stays at `v_full_initial`. A persisted `v_full` across reboots would
  remove that cold-start bias.
- **Chemistry mismatch**: The current header comment says "3S LiPo (9V dead,
  12.6V full)" but `notes.md` and observed telemetry indicate a 12V sealed
  lead-acid. Aligning the comment with confirmed hardware would reduce confusion.
