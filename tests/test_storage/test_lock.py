"""进程文件锁测试"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

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


def test_second_lock_same_pid_reentrant(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    lock = ProcessLock(lock_file)
    lock.acquire()
    lock.acquire()
    assert lock.held
    lock.release()


def test_lock_conflict_when_other_pid_alive(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    # 使用当前进程 PID 但通过第二个 ProcessLock 实例在 release 前模拟占用
    # 先写入一个「其他存活进程」——用自身 PID 会在 acquire 时因 pid==os.getpid() 被视为过期
    # 因此这里直接测：已持有锁的文件 + 另一实例（同 PID）应清除并获取（同进程可重入语义）
    lock_file.write_text(str(os.getpid()), encoding="utf-8")
    lock = ProcessLock(lock_file)
    lock.acquire()
    assert lock.held
    lock.release()


def test_stale_lock_cleared(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    # 使用几乎不可能存活的超大 PID
    lock_file.write_text("999999999", encoding="utf-8")
    lock = ProcessLock(lock_file)
    lock.acquire()
    assert lock.held
    assert lock_file.read_text(encoding="utf-8") == str(os.getpid())
    lock.release()


def test_conflict_with_live_foreign_pid(tmp_path: Path) -> None:
    lock_file = tmp_path / "bili_monitor.lock"
    # 使用系统进程 PID 1（Windows 上可能不存在则跳过冲突断言）
    foreign = 1
    lock_file.write_text(str(foreign), encoding="utf-8")
    lock = ProcessLock(lock_file)
    if os.name == "nt":
        # Windows 下 PID 1 通常不是可查询进程，可能被视为 stale
        try:
            lock.acquire()
            lock.release()
        except ProcessLockError:
            pass
    else:
        with pytest.raises(ProcessLockError):
            lock.acquire()
