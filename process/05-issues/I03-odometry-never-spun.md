# I03 Odometry subscription never runs; movement is open-loop only

* **Symptom**: `MovementApi.current_pose` is always `None`; movement accuracy
  depends entirely on `time.sleep` timing. `MovementApi` subscribes to `/odom`
  (`ros2_api/movement_api.py:24`) and stores pose in `odom_callback` (`:148`), but
  no executor ever spins that node. The only spinning in the CLI path is
  `IntentApi.publish` doing `spin_once(self)` on its own node
  (`ros2_api/intent_api.py:43`), so `odom_callback` never fires.
* **Tests done**: Code read; confirmed by tracing the call graph — no
  `spin`/executor covers the movement node.
* **Latest theory**: Run a background executor (or a single-threaded spin thread)
  that owns all the API nodes, then convert distance/turn to closed-loop on
  `current_pose`. Removes the dead-reckoning error and unblocks I04's root cause.
