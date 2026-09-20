"""进程文件锁测试"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from bili_monitor.storage import lock as lock_mod
from bili_monitor.storage.lock import ProcessLock, ProcessLockError, lock_path_for_database


def test_lock_path_for_database() -> None:
    assert lock_path_for_database("data/bili_monitor.db") == Path("data/bili_monitor.lock")


def test_acquire_and_release(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    lock = ProcessLock(lock_file)
    lock.acquire()
    assert lock.held
    assert lock_file.read_text(encoding="utf-8") == str(os.getpid())
    lock.release()
    assert not lock_file.exists()


def test_acquire_idempotent_same_instance(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    lock = ProcessLock(lock_file)
    lock.acquire()
    lock.acquire()
    assert lock.held
    lock.release()


def test_stale_lock_cleared(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    lock_file.write_text("999999999", encoding="utf-8")
    lock = ProcessLock(lock_file)
    lock.acquire()
    assert lock.held
    assert lock_file.read_text(encoding="utf-8") == str(os.getpid())
    lock.release()


def test_conflict_when_foreign_pid_alive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """锁文件被其他存活进程占用时，第二次 acquire 必须失败"""
    lock_file = tmp_path / "bili_monitor.lock"
    lock_file.write_text("424242", encoding="utf-8")
    monkeypatch.setattr(lock_mod, "_pid_alive", lambda pid: pid == 424242)
    lock = ProcessLock(lock_file)
    with pytest.raises(ProcessLockError) as exc:
        lock.acquire()
    assert "424242" in str(exc.value)
    assert not lock.held
    assert lock_file.exists()


def test_release_only_own_pid(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    lock = ProcessLock(lock_file)
    lock.acquire()
    lock_file.write_text("999999999", encoding="utf-8")
    lock.release()
    # 非本进程 PID 的锁文件不应被误删
    assert lock_file.exists()
    assert not lock.held
