# I01 ProcessApi concurrent pipe read corrupts output and truncates logs

* **Symptom**: When a launched process is stopped, captured output can be lost or
  garbled and its log file ends up nearly empty. `kill_process` calls
  `proc_info.process.communicate()` (`ros2_api/process_api.py:310`) while the
  `_capture_output` daemon thread is still looping on `process.stdout.readline()`
  (`:394`) — two readers on one pipe. Then `:315` reopens the same log file in
  `"w"`, truncating everything the capture thread already wrote.
* **Tests done**: Code read only; not yet reproduced under instrumentation.
* **Latest theory**: Single-writer ownership of the pipe and the log file. Let the
  capture thread own stdout and the log; have `kill_process` only signal + join the
  thread (no second `communicate()`/`open("w")`). Fix together with I02.
