"""Tests for UPS stats collection (feature F17, task TF17-T03)."""
from dome_control.ups_status import battery_percent, read_ups_stats


class FakeINA219:
    """Mock INA219 returning fixed readings."""

    def __init__(self, bus_v, current_ma, power_w):
        self._bus_v = bus_v
        self._current_ma = current_ma
        self._power_w = power_w

    def getBusVoltage_V(self):
        return self._bus_v

    def getCurrent_mA(self):
        return self._current_ma

    def getPower_W(self):
        return self._power_w


def test_unit_conversions():
    stats = read_ups_stats(FakeINA219(bus_v=12.0, current_ma=500.0, power_w=6.0))
    assert stats.bus_voltage_v == 12.0
    assert stats.current_a == 0.5          # mA -> A
    assert stats.power_w == 6.0


def test_percent_linear_map():
    # 9V -> 0%, 12.6V -> 100%, midpoint 10.8V -> 50%
    assert abs(battery_percent(9.0) - 0.0) < 1e-6
    assert abs(battery_percent(12.6) - 100.0) < 1e-6
    assert abs(battery_percent(10.8) - 50.0) < 1e-6


def test_percent_clamped():
    assert battery_percent(8.0) == 0.0     # below empty
    assert battery_percent(13.5) == 100.0  # above full


def test_percent_in_stats():
    stats = read_ups_stats(FakeINA219(bus_v=10.8, current_ma=0.0, power_w=0.0))
    assert abs(stats.percent - 50.0) < 1e-6


def test_negative_current_is_charging():
    stats = read_ups_stats(FakeINA219(bus_v=12.6, current_ma=-300.0, power_w=4.0))
    assert stats.current_a == -0.3
