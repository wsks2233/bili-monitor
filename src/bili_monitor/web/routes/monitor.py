"""监控相关路由"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from ...config.loader import load_config
from ...monitor.runner import Monitor

logger = logging.getLogger("bili-monitor.web")

monitor_bp = Blueprint("monitor", __name__)


@monitor_bp.route("/api/start", methods=["POST"])
def start_monitor() -> Any:
    """启动监控"""
    try:
        from ...storage.lock import ProcessLockError, lock_path_for_database

        monitor: Monitor | None = current_app.config.get("MONITOR_INSTANCE")

        if monitor and monitor._running:
            return jsonify({"error": "监控已在运行中"}), 400

        config_path = current_app.config["CONFIG_PATH"]
        config = load_config(config_path)

        event_bus = current_app.config["EVENT_BUS"]
        lock_path = str(lock_path_for_database(config.database.path))
        from ...storage.lock import ProcessLock

        lock = ProcessLock(lock_path, logger)
        try:
            lock.acquire()
        except ProcessLockError as e:
            return jsonify({"error": str(e), "code": "monitor_locked"}), 409

        monitor = Monitor(
            config,
            logger,
            on_event=lambda e: event_bus.publish(e),
            config_path=config_path,
            lock_path=lock_path,
        )
        monitor._lock = lock
        current_app.config["MONITOR_INSTANCE"] = monitor
        current_app.config["START_TIME"] = datetime.now()

        def run_monitor() -> None:
            try:
                monitor.run()
            except ProcessLockError as e:
                logger.error(f"监控启动被拒绝: {e}")
                current_app.config["MONITOR_INSTANCE"] = None
            except Exception as e:
                logger.error(f"监控运行错误: {e}")
                current_app.config["MONITOR_INSTANCE"] = None
            finally:
                # 兜底：run() 内 finally 会释放；此处防止异常路径留下活 PID 锁
                lock_obj = getattr(monitor, "_lock", None)
                if lock_obj is not None and getattr(lock_obj, "held", False):
                    try:
                        lock_obj.release()
                    except Exception:
                        pass
                    monitor._lock = None

        thread = threading.Thread(target=run_monitor, daemon=True)
        thread.start()

        return jsonify({"success": True, "message": "监控已启动"})

    except Exception as e:
        logger.error(f"启动监控失败: {e}")
        return jsonify({"error": str(e)}), 500


@monitor_bp.route("/api/stop", methods=["POST"])
def stop_monitor() -> Any:
    """停止监控"""
    try:
        monitor: Monitor | None = current_app.config.get("MONITOR_INSTANCE")

        if not monitor or not monitor._running:
            return jsonify({"error": "监控未在运行"}), 400

        monitor.stop()
        current_app.config["START_TIME"] = None

        return jsonify({"success": True, "message": "监控已停止"})

    except Exception as e:
        logger.error(f"停止监控失败: {e}")
        return jsonify({"error": str(e)}), 500


@monitor_bp.route("/api/stats")
def get_stats() -> Any:
    """获取统计信息"""
    monitor: Monitor | None = current_app.config.get("MONITOR_INSTANCE")

    if not monitor:
        return jsonify({})

    return jsonify(monitor.get_stats())


@monitor_bp.route("/api/logs")
def get_logs() -> Any:
    """获取运行日志"""
    try:
        config_path = current_app.config["CONFIG_PATH"]
        config = load_config(config_path)
        log_file = Path(config.logger.file)

        if not log_file.exists():
            return jsonify({"logs": []})

        limit = request.args.get("limit", 100, type=int)
        lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()

        return jsonify({"logs": lines[-limit:]})

    except Exception as e:
        logger.error(f"读取日志失败: {e}")
        return jsonify({"logs": [], "error": str(e)})
