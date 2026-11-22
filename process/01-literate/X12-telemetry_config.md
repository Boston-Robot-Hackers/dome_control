---
version: "1.0"
generated: "2026-11-22"
---

# Appendix X12 — telemetry config loader

`telemetry/config.py` loads `config/telemetry.yaml` for the telemetry node
and always returns three values: `publish_rate_hz`, `log_interval_s` and
`max_log_files`.

```python
def positive_float(raw, key, default):
    val = raw.get(key, default)
    try:
        val = float(val)
    except (TypeError, ValueError):
        return default
    return val if val > 0 else default
```

A missing file, missing key, unparseable value or non-positive value all
fall back to the default. The file may hold either a `telemetry:` block or
a flat mapping.

## Observations

- **Bad values are silently replaced.** This is the guess-and-repair
  pattern the style guide forbids. `publish_rate_hz: 0` or a typo such as
  `publish_rate_hz: "1Hz"` quietly becomes 1 Hz, and the operator never
  learns their setting was ignored. Raise a `ValueError` naming the key,
  or at least log a warning at node startup.
- **There are two accepted layouts.** Supporting both a `telemetry:` block
  and a flat mapping doubles what has to be documented. Pick one.
- **The file has no shebang**, against the style guide's MUST.
