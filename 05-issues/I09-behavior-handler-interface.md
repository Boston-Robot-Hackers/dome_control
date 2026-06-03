# I09 Behavior handlers use the same signature two opposite ways

* **Symptom**: `execute(intent, node)` means different things per handler, which is
  error-prone. `MotionBehavior.execute` uses the passed `node` arg and ignores its
  stored `self.rc`/self (`behaviors/motion_behavior.py:24`); `PerceptionBehavior.execute`
  ignores the `node` arg and uses `self.node` (`behaviors/perception_behavior.py:22`).
  One was constructed with the controller, the other with the node.
* **Tests done**: Code read only.
* **Latest theory**: Define a `Behavior` base class with one explicit contract
  (what's injected at construction vs passed to `execute`), and make both handlers
  conform. Also fixes the split import of `make_announcement_msg` (I11).
