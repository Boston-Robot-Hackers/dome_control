"""Tests for UPS stats collection (feature F17, task TF17-T03)."""
from dome_control.ups_status import SocEstimator, V_EMPTY_DEFAULT, V_FULL_DEFAULT, read_ups_stats


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
    est = SocEstimator()
    stats = read_ups_stats(FakeINA219(bus_v=12.0, current_ma=500.0, power_w=6.0), est)
    assert stats.bus_voltage_v == 12.0
    assert stats.current_a == 0.5          # mA -> A
    assert stats.power_w == 6.0


def test_soc_at_boundaries():
    # At v_empty -> 0%, at v_full_initial -> 100%
    est = SocEstimator()
    assert est.estimate(V_EMPTY_DEFAULT) == 0.0
    assert est.estimate(V_FULL_DEFAULT) == 100.0


def test_soc_midpoint():
    est = SocEstimator()
    mid = (V_EMPTY_DEFAULT + V_FULL_DEFAULT) / 2
    assert abs(est.estimate(mid) - 50.0) < 0.2


def test_soc_clamped():
    est = SocEstimator()
    assert est.estimate(8.0) == 0.0       # below empty
    assert est.estimate(15.0) == 100.0    # above full (also updates v_full)


def test_soc_session_peak_updates_v_full():
    # If we observe a higher voltage, v_full rises and subsequent % drops
    est = SocEstimator(v_full_initial=12.18)
    est.estimate(13.0)                    # peak now 13.0
    assert est.v_full == 13.0
    soc = est.estimate(12.18)
    assert soc < 100.0                    # 12.18 is no longer 100%


def test_r_int_correction():
    # With R_INT set, discharging current (positive) reduces apparent voltage
    est = SocEstimator(r_int=0.5)
    soc_no_load = est.estimate(11.0, current=0.0)
    soc_under_load = SocEstimator(r_int=0.5).estimate(11.0, current=0.5)
    assert soc_under_load > soc_no_load   # corrected voltage is higher


def test_percent_in_stats():
    est = SocEstimator()
    mid = (V_EMPTY_DEFAULT + V_FULL_DEFAULT) / 2
    stats = read_ups_stats(FakeINA219(bus_v=mid, current_ma=0.0, power_w=0.0), est)
    assert abs(stats.percent - 50.0) < 0.2


def test_negative_current_is_charging():
    est = SocEstimator()
    stats = read_ups_stats(FakeINA219(bus_v=12.6, current_ma=-300.0, power_w=4.0), est)
    assert stats.current_a == -0.3
