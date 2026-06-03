# I12 UPS/host telemetry imports hardware SDK, violating the no-hardware spec

* **Symptom**: `dome_control` reads hardware directly, against its own spec.
  `spec.md:25-27` states: "this package only publishes/subscribes. **Never import
  hardware SDKs directly.**" But:
  - `ups_status.py` imports `smbus` and reads the INA219 UPS over I2C (entered in
    commit `b6eb73e`, "added ups_status from INA UPS").
  - `nodes/telemetry_node.py` opens that I2C device and reads host `/proc`, `/sys`
    directly (feature F17). Note: F17 already does the *right* thing for OAK — it
    subscribes to `/telemetry/oak` instead of opening the camera — but does the
    opposite for UPS/host.
* **Tests done**: Confirmed by reading `spec.md` and the telemetry code; INA219
  read verified live on hardware during F17.
* **Latest theory**: Per the package's layering intent, hardware belongs behind a
  ROS2 topic. Move the INA219 + host reads into a small robot-side publisher node
  (mirroring how `dome_vision` owns the OAK and publishes `/telemetry/oak`), and have
  `dome_control`'s telemetry node *subscribe* to a `/telemetry/ups` (+ host) topic
  and only merge/republish/log. Decision needed: where that publisher node lives
  (separate hardware package vs. an explicitly-allowed exception in this package).
