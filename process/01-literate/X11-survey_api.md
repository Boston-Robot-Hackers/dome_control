---
version: "2.0"
generated: "2026-11-22"
---

# Appendix X11 — SurveyApi

`ros2_api/survey_api.py` is a minimal Trigger-service client for
`/survey/start`:

```python
def start(self, timeout_s: float = 5.0) -> tuple[bool, str]:
    if not self._client.wait_for_service(timeout_sec=timeout_s):
        return (False, "/survey/start service not available — is spin_survey_node running?")
    future = self._client.call_async(Trigger.Request())
    rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_s)
    if not future.done():
        return False, "Service call timed out"
    result = future.result()
    return result.success, result.message
```

In a CLI process that isn't otherwise spinning, `spin_until_future_complete`
is the right way to make a synchronous call.

It is the only API that subclasses `Node` directly instead of `BaseApi`, so
it takes no config.

## Observations

- **A timed-out future is left pending.** When `spin_until_future_complete`
  times out, the future isn't cancelled, and a late response arrives
  orphaned. Call `future.cancel()` and the client's `remove_pending_request`.
- **`self._client` breaks the "no leading underscore" rule.**
- **It is inconsistent with the other APIs.** It's the only one outside
  `BaseApi`. Either it's the better pattern (plain node, no config), or it
  should join the family.
