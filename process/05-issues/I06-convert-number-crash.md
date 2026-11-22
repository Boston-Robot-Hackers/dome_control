# I06 ConfigManager.convert_number crashes on valid float literals

* **Symptom**: `config set <name> 1e5` (or `inf`, `1_000`) raises and aborts the set.
  `convert_number` (`commands/config_manager.py:47`) returns `int(value)` when the
  string has no `"."`, but `is_number` accepted it via `float()` first
  (`:52`), so `int("1e5")` raises `ValueError`.
* **Tests done**: Code read only.
* **Latest theory**: Coerce with float-first then int-if-integral, or reuse the
  hardened `positive_float`/`positive_int` style from `telemetry/config.py`.
  Numeric coercion is reimplemented in three places (`convert_number`,
  `command_dispatcher.parse_value`, `telemetry/config`) — consolidate. See I11.
