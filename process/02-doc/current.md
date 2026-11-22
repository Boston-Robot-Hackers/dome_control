# control — Current Session Handoff

## Open

### Pick up here (2026-11-22)

- Kit sync and `process/` move committed (see `history.md`). The new
  SessionStart hook, `/feature` and `/close-feature` are live from now on.
- **Next:** resume dome2 F05 (below).

### Next

- **dome2 F05, launch-file cleanup**
  (`dome2/process/03-features/notdone/F05-launch-file-cleanup.md`):
  TF05.0–TF05.4 done. Left: TF05.5 (stack docs), TF05.6 (convention test
  suite, in progress), TF05.7 (robot + remote verification), and a live
  clean-stop check of dome_control's nodes.
- Test `scene describe` / `scene objects` with real OAK hardware.
- Observe the empty-turn voice debug log on hardware.
- Split `RobotController` into smaller modules.

### Decisions pending

- **Uncommitted `angular_speed` 1.5 → 1.0** in `config/control-config.yaml`:
  predates the 2026-11-22 session and was left out of its commit. Keep or
  revert.
- **dome_vision link fixes uncommitted:** two `dome_control/process/02-doc`
  path updates in `../dome_vision/process/02-doc/` (`system-overview.md`,
  `house-map.md`). Commit in that repo.
- **F16 status mismatch:** `F16-list-detected-objects.md` says not done, but
  `PerceptionBehavior` already handles `list_objects` and caches
  `/oak/detections`. Close it or define what is left.
- **Stale voice task files:** `process/04-tasks/notdone/` holds TF05, TF08,
  TF09, TF11, whose features are in `process/03-features/deferred/`. They
  likely belong in `dome_voice`. TF05 also collides by name with dome2's F05.

### Chores

Open entries in `process/04-tasks/chores.md`:

- Duplicate `intent.*` CLI commands.
- Real `CommandDef`s for `scene.*`.
- `config.set` stores `0`/`1` as booleans.
- Stale README command list.
- Add a `Makefile` (the synced style guide now requires one).

### Blocked

- **Doppler token missing:** the session shell skips secrets, so
  `ROBOFLOW_API_KEY` is unset and `dome_vision` won't relaunch. Not a
  dome_control fix.

### Unconfirmed on hardware

- **Empty STT turns:** `voice_input_node` debug log shows
  `floor`/`cutoff`/`command_started`/`raw_text`; needs a hardware run.
- **Wake re-trigger:** the cooldown fix is unconfirmed.

### Open issues

- **Untriaged:** `process/05-issues/` holds I01–I14 flat, with no
  `open/`/`closed/`/`deferred/` split and no status field. Some look already
  resolved (I10 lint gate by the ruff pass; I12 hardware SDK by F20). Sort
  them before relying on any.
