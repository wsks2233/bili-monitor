"""进程文件锁：防止 CLI 与 Web 同时启动多份监控"""

from __future__ import annotations

import logging
import os
from pathlib import Path


class ProcessLockError(Exception):
    """获取进程锁失败"""


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class ProcessLock:
    """基于锁文件的单实例锁（内容为持有进程 PID）"""

    def __init__(self, path: str | Path, logger: logging.Logger | None = None) -> None:
        self.path = Path(path)
        self._logger = logger or logging.getLogger("bili-monitor.lock")
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    def acquire(self) -> None:
        if self._held:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    raw = self.path.read_text(encoding="utf-8").strip()
                    pid = int(raw) if raw else 0
                except (OSError, ValueError):
                    pid = 0
                if pid and pid != os.getpid() and _pid_alive(pid):
                    raise ProcessLockError(
                        f"监控已在运行 (PID={pid})，锁文件: {self.path}"
                    ) from None
                self._logger.warning(f"清除过期监控锁 {self.path} (PID={pid})")
                try:
                    self.path.unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            try:
                os.write(fd, str(os.getpid()).encode("utf-8"))
            finally:
                os.close(fd)
            self._held = True
            self._logger.info(f"已获取监控锁: {self.path} (PID={os.getpid()})")
            return
        raise ProcessLockError(f"无法获取监控锁: {self.path}")

    def release(self) -> None:
        if not self._held:
            return
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if raw == str(os.getpid()):
                self.path.unlink(missing_ok=True)
        except OSError as e:
            self._logger.warning(f"释放监控锁失败: {e}")
        self._held = False
        self._logger.info(f"已释放监控锁: {self.path}")


def lock_path_for_database(db_path: str | Path) -> Path:
    """根据数据库路径推导锁文件位置（与 DB 同目录）"""
    return Path(db_path).parent / "bili_monitor.lock"
