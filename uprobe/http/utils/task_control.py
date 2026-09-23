from __future__ import annotations

import json
import os
import signal
from pathlib import Path
from typing import Any


CONTROL_FILENAME = ".task-process.json"


def _process_start_time(pid: int) -> str:
    """Return Linux's stable process start tick for PID reuse protection."""
    stat_path = Path("/proc") / str(pid) / "stat"
    fields = stat_path.read_text(encoding="utf-8").split()
    return fields[21]


def _control_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / CONTROL_FILENAME


def register_task_process(
    output_dir: str | Path, *, task_id: str, username: str
) -> dict[str, Any]:
    """Put a process-pool worker in its own group and publish its identity."""
    if os.name != "posix":
        raise RuntimeError("Task pause/resume is supported only on POSIX systems")

    pid = os.getpid()
    if os.getpgrp() != pid:
        os.setsid()
    payload = {
        "pid": pid,
        "pgid": os.getpgrp(),
        "start_time": _process_start_time(pid),
        "task_id": task_id,
        "username": username,
    }
    path = _control_path(output_dir)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload), encoding="utf-8")
    temp_path.replace(path)
    return payload


def cleanup_task_process(output_dir: str | Path) -> None:
    _control_path(output_dir).unlink(missing_ok=True)


def signal_task_process(
    output_dir: str | Path,
    sig: signal.Signals,
    *,
    task_id: str,
    username: str,
) -> None:
    """Signal a verified task process group without risking a reused PID."""
    path = _control_path(output_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError("Task worker is not ready or no longer running") from exc
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError("Task worker control data is invalid") from exc

    if payload.get("task_id") != task_id or payload.get("username") != username:
        raise RuntimeError("Task worker identity does not match this task")

    try:
        pid = int(payload["pid"])
        pgid = int(payload["pgid"])
        start_time = str(payload["start_time"])
        if pgid != pid or _process_start_time(pid) != start_time:
            raise RuntimeError("Task worker is no longer running")
        os.killpg(pgid, sig)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise RuntimeError("Task worker is no longer running") from exc


def pause_task_process(
    output_dir: str | Path, *, task_id: str, username: str
) -> None:
    signal_task_process(
        output_dir, signal.SIGSTOP, task_id=task_id, username=username
    )


def resume_task_process(
    output_dir: str | Path, *, task_id: str, username: str
) -> None:
    signal_task_process(
        output_dir, signal.SIGCONT, task_id=task_id, username=username
    )
