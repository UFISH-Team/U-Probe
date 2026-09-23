import os
import signal
import time
from multiprocessing import Pipe, Process
from pathlib import Path

import pytest

from uprobe.http.utils import task_control


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX process signals required")


def _registered_worker(output_dir: str, connection) -> None:
    task_control.register_task_process(
        output_dir, task_id="task-live", username="alice"
    )
    connection.send(os.getpid())
    while True:
        time.sleep(0.05)


def _process_state(pid: int) -> str:
    return (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8").split()[2]


def _wait_for_state(pid: int, predicate, timeout: float = 2.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = _process_state(pid)
        if predicate(state):
            return state
        time.sleep(0.02)
    raise AssertionError(f"Process {pid} did not reach the expected state")


def test_signal_task_process_validates_identity(tmp_path: Path, monkeypatch):
    control = tmp_path / task_control.CONTROL_FILENAME
    control.write_text(
        '{"pid": 123, "pgid": 123, "start_time": "42", '
        '"task_id": "task-1", "username": "alice"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(task_control, "_process_start_time", lambda pid: "42")
    sent = []
    monkeypatch.setattr(os, "killpg", lambda pgid, sig: sent.append((pgid, sig)))

    task_control.pause_task_process(tmp_path, task_id="task-1", username="alice")
    task_control.resume_task_process(tmp_path, task_id="task-1", username="alice")

    assert sent == [(123, signal.SIGSTOP), (123, signal.SIGCONT)]


def test_signal_task_process_rejects_wrong_task(tmp_path: Path):
    control = tmp_path / task_control.CONTROL_FILENAME
    control.write_text(
        '{"pid": 123, "pgid": 123, "start_time": "42", '
        '"task_id": "task-1", "username": "alice"}',
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="identity"):
        task_control.pause_task_process(
            tmp_path, task_id="task-other", username="alice"
        )


def test_cleanup_task_process(tmp_path: Path):
    control = tmp_path / task_control.CONTROL_FILENAME
    control.write_text("{}", encoding="utf-8")

    task_control.cleanup_task_process(tmp_path)

    assert not control.exists()


def test_pause_and_resume_live_worker(tmp_path: Path):
    parent_connection, child_connection = Pipe(duplex=False)
    worker = Process(target=_registered_worker, args=(str(tmp_path), child_connection))
    worker.start()
    pid = parent_connection.recv()
    try:
        task_control.pause_task_process(
            tmp_path, task_id="task-live", username="alice"
        )
        assert _wait_for_state(pid, lambda state: state == "T") == "T"

        task_control.resume_task_process(
            tmp_path, task_id="task-live", username="alice"
        )
        assert _wait_for_state(pid, lambda state: state != "T") != "T"
    finally:
        try:
            os.killpg(pid, signal.SIGCONT)
        except ProcessLookupError:
            pass
        worker.terminate()
        worker.join(timeout=2)
