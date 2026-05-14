---
version: "1.0"
generated: "2026-05-14"
---

# SurveyApi: /survey/start Service Client

`SurveyApi` is a thin ROS2 `Node` that calls the `/survey/start` Trigger service on behalf of the CLI. It follows the same pattern as other `*Api` classes: construct, call, return `(success, message)`.

## Usage

```python
api = SurveyApi()
ok, msg = api.start(timeout_s=5.0)
```

## Implementation

```python
class SurveyApi(Node):
    def __init__(self):
        super().__init__("survey_api_client")
        self._client = self.create_client(Trigger, "/survey/start")

    def start(self, timeout_s=5.0) -> tuple[bool, str]:
        if not self._client.wait_for_service(timeout_sec=timeout_s):
            return False, "/survey/start service not available"
        future = self._client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_s)
        if not future.done():
            return False, "Service call timed out"
        result = future.result()
        return result.success, result.message
```

`wait_for_service` blocks up to `timeout_s` for `SpinSurveyNode` to appear. `spin_until_future_complete` blocks for the round-trip. Both timeouts use the same value. The caller (`RobotController.start_survey`) wraps the result in a `CommandResponse`.

## Notes

- `SurveyApi` is created lazily by `RobotController` (same pattern as `MovementApi`, `SpeechApi`).
- If `SpinSurveyNode` is not running, `wait_for_service` returns False after timeout and an error message is returned to the CLI.
