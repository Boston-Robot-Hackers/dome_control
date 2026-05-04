---
version: "1.1"
generated: "2026-05-04"
---

# ProcessApi: Subprocess Lifecycle Management

`ProcessApi` owns everything that involves spawning, monitoring, and killing OS-level processes. It has two distinct modes of operation: **async launch** (fire-and-forget background processes) and **sync execution** (blocking commands that return output). Both are used by `RobotController` for different purposes.

## Data Structures

Two dataclasses carry all process state:

```python
@dataclass
class ProcessInfo:
    process: subprocess.Popen
    command: str
    output: List[str]
    is_running: bool
    pid: int
    start_time: float
    log_file: Optional[str] = None

@dataclass
class LaunchConfig:
    launch_type: str
    command_template: str
    description: str
    default_params: Dict[str, str]
```

`ProcessInfo` is the runtime state of a running process. `LaunchConfig` is the static template loaded from YAML config.

```
                   config.yaml
                       │
            ┌──────────▼──────────┐
            │   LaunchConfig[]    │ (templates, loaded at init)
            └──────────┬──────────┘
                       │ launch_by_type()
            ┌──────────▼──────────┐
            │    ProcessInfo[]    │ (live processes, in self.processes dict)
            └─────────────────────┘
```

## Loading Launch Templates

`ProcessApi.__init__` calls `_load_launch_configs` to convert the raw YAML dict into typed `LaunchConfig` objects:

```python
def _load_launch_configs(self):
    templates = self.config.get_launch_templates() if self.config else {}
    self.launch_configs = {}
    for launch_type, template in templates.items():
        self.launch_configs[launch_type] = LaunchConfig(
            launch_type=launch_type,
            command_template=template.get("command", ""),
            description=template.get("description", ""),
            default_params=template.get("default_params", {})
        )
```

## Async Launch: launch_command

The async path launches a process in a new session (`start_new_session=True`) so it survives terminal disconnection. A background thread captures all stdout to a log file and to the console:

```python
proc = subprocess.Popen(
    command, shell=True,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    text=True, bufsize=1,
    start_new_session=True,
)
```

`start_new_session=True` creates a new process group, which matters for `kill_ros_process`: if the PID is the group leader, `SIGTERM` is sent to `-pgid` (the whole group), not just the parent.

A UUID is returned as the process handle. `RobotController` stores this UUID in `launch_process_ids` keyed by launch type.

## Sync Execution: run_command_sync

Map saving and serialization need to run a command and wait for its result. `CommandConfig` bundles command, log name, and timeout:

```python
@dataclass
class CommandConfig:
    command: str
    log_name: Optional[str]
    timeout: float
```

```python
def run_command_sync(self, config: CommandConfig) -> tuple[bool, str, Optional[str]]:
    result = subprocess.run(
        config.command, shell=True,
        capture_output=True, text=True,
        timeout=config.timeout
    )
    return (result.returncode == 0, result.stdout + result.stderr, log_file_path)
```

Returns `(success, output, log_file_path)` so callers can report both the outcome and where to find details.

## Killing Processes

`kill_ros_process` handles the case where the target may be a process group leader — in which case `kill -TERM -PID` sends SIGTERM to the entire group:

```python
target = f"-{pid}" if is_group_leader else str(pid)
subprocess.run(["kill", "-TERM", target], check=True, timeout=2)
```

If SIGTERM fails, it escalates to SIGKILL. This graceful-then-force pattern avoids leaving zombie processes.

## Process Status Queries

`is_process_running` uses `poll()` to detect silent process death without blocking:

```python
def is_process_running(self, process_id: str) -> bool:
    proc_info = self.processes[process_id]
    proc_info.process.poll()
    if proc_info.process.returncode is not None:
        proc_info.is_running = False
        return False
    return True
```

`get_process_pid` provides the OS PID for external display:

```python
def get_process_pid(self, process_id: str) -> int | str:
    info = self.processes.get(process_id)
    return info.pid if info else "unknown"
```

## Listing ROS and Launch Processes

`list_ros_processes` and `list_launch_processes` shell out to `ps aux` and `ps axo` respectively, filtering by ROS-related keywords. These are display-only utilities — they scan all OS processes, not just managed ones:

```
ps aux → filter ros/nav2/slam/rviz keywords → tabular output
ps axo pid,pgid,ppid → filter ros2 launch → parent-only display
```

## Observations

- **Parameter formatting is complex.** `launch_by_type` has distinct code paths for `bl` commands, `ros2 run`, and launch files. This fragility could be replaced with a strategy object per command type.
- **`list_ros_processes` leaks shell knowledge.** The hardcoded keyword list `["ros2", "nav2", "slam", "rviz", ...]` will miss new components and is not tested.
- **Circular import via string.** `kill_ros_process` and `list_*` import `CommandResponse` inline to avoid circular imports. The fix is to move `CommandResponse` to its own module.
