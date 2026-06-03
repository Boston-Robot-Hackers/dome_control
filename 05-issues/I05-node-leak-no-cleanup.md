# I05 ROS2 nodes leak; CLI never cleans them up

* **Symptom**: Each CLI run leaks ROS nodes and DDS participants. `RobotController`
  lazily creates six nodes via `@property` (`commands/robot_controller.py:43-80`);
  only `ProcessApi.destroy_node` does cleanup (`ros2_api/process_api.py:541`), and
  `SimpleCLI` never destroys any node on exit (`interface/simple_cli.py:304`).
* **Tests done**: Code read only.
* **Latest theory**: Give `RobotController` a `shutdown()` that destroys every
  instantiated node, and call it from the CLI `finally`/exit path. Pairs naturally
  with the executor work in I03 (one owner of node lifecycle).
