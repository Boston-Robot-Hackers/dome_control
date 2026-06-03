# I08 Intent handlers have no-op/stub actions and no single registry

* **Symptom**: Some intents do nothing or are unreachable. Note: two *vocabularies*
  is partly **by design** — `00-overview.md` ("Intent over raw commands") decouples
  the voice action set from the CLI command set, so `dome_voice` legitimately emits
  motion intents (`turn_right`, `drive_square`, `get_status`) that the CLI does not.
  The real problems are:
  - `explore` is a silent no-op (`behaviors/motion_behavior.py:31`).
  - `count_objects` only logs "not yet implemented"
    (`behaviors/perception_behavior.py:28`) though the CLI advertises
    `scene.count` / `intent.count_objects` (`commands/command_dispatcher.py:60`).
  - No single source of truth lists the full intent set, its slots, and which
    handler owns it — so CLI names, behavior names, and voice names drift silently.
* **Tests done**: Code read; both name sets compared. Confirm with `dome_voice`
  before changing the voice-side names.
* **Latest theory**: Keep the decoupling, but add one shared intent registry
  (name → slots → owning handler) as the documented contract, and either implement
  or remove the stub handlers. Pairs with I09 (handler interface).
