"""Tests for host stats collection (feature F17, task TF17-T07)."""
from dome_control.telemetry.host_stats import (
    HostStatsReader,
    cpu_pct_from_deltas,
    parse_cpu_temp_c,
    parse_cpu_totals,
    parse_mem_used_mb,
    parse_uptime_s,
)

STAT_A = "cpu  100 0 100 700 100 0 0 0\ncpu0 1 2 3 4\n"
# +50 busy (user), +50 idle -> 100 total delta, 50 idle delta -> 50% busy
STAT_B = "cpu  150 0 100 750 100 0 0 0\ncpu0 1 2 3 4\n"

MEMINFO = "MemTotal:        4096000 kB\nMemAvailable:    1048576 kB\nBuffers: 1 kB\n"


def test_parse_cpu_temp():
    assert parse_cpu_temp_c("41778\n") == 41.778


def test_parse_cpu_totals():
    idle, total = parse_cpu_totals(STAT_A)
    assert idle == 700 + 100          # idle + iowait
    assert total == 100 + 0 + 100 + 700 + 100


def test_parse_cpu_totals_missing():
    assert parse_cpu_totals("intr 1 2 3\n") == (0, 0)


def test_cpu_pct_from_deltas():
    prev = parse_cpu_totals(STAT_A)
    cur = parse_cpu_totals(STAT_B)
    assert abs(cpu_pct_from_deltas(prev, cur) - 50.0) < 1e-6


def test_cpu_pct_no_elapsed():
    assert cpu_pct_from_deltas((10, 100), (10, 100)) == 0.0


def test_parse_mem_used_mb():
    # (4096000 - 1048576) kB = 3047424 kB / 1024 = 2976 MB
    assert abs(parse_mem_used_mb(MEMINFO) - 2976.0) < 1e-6


def test_parse_mem_missing_fields():
    assert parse_mem_used_mb("Foo: 1 kB\n") == 0.0


def test_parse_uptime():
    assert parse_uptime_s("7200.42 14000.10\n") == 7200.42


def test_reader_first_tick_cpu_zero_then_real():
    files = {"/t": "41778\n", "/s": STAT_A, "/m": MEMINFO, "/u": "7200.0 1.0\n"}
    reader = HostStatsReader(
        temp_path="/t", stat_path="/s", meminfo_path="/m", uptime_path="/u",
        read_text=lambda p: files[p],
    )
    first = reader.read()
    assert first.cpu_pct == 0.0           # no prior sample
    assert first.cpu_temp_c == 41.778
    assert abs(first.mem_used_mb - 2976.0) < 1e-6
    assert first.uptime_s == 7200.0

    files["/s"] = STAT_B                   # advance the cpu sample
    second = reader.read()
    assert abs(second.cpu_pct - 50.0) < 1e-6


def test_reader_missing_files_zero():
    reader = HostStatsReader(read_text=lambda p: None)
    stats = reader.read()
    assert stats.cpu_temp_c == 0.0
    assert stats.cpu_pct == 0.0
    assert stats.mem_used_mb == 0.0
    assert stats.uptime_s == 0.0
