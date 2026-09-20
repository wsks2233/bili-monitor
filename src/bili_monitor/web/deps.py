"""Web 层共享依赖：数据库访问不绑定进程内 Monitor"""

from __future__ import annotations

import logging
from typing import Any

from flask import current_app

logger = logging.getLogger("bili-monitor.web")


def get_database() -> Any:
    """返回可用的 Database：优先 Monitor 实例，否则按配置独立打开。"""
    monitor = current_app.config.get("MONITOR_INSTANCE")
    if monitor is not None:
        db = getattr(monitor, "_db", None)
        if db is not None:
            return db

    db = current_app.config.get("WEB_DB")
    if db is not None:
        return db

    from pathlib import Path

    from ..config.loader import load_config
    from ..storage.database import Database

    config = current_app.config.get("APP_CONFIG")
    if config is None:
        config = load_config(current_app.config["CONFIG_PATH"])
        current_app.config["APP_CONFIG"] = config

    config_path = current_app.config.get("CONFIG_PATH") or "config.yaml"
    images_base = Path(config_path).parent / "images"
    db = Database(config=config.database, logger=logger, images_base=images_base)
    current_app.config["WEB_DB"] = db
    return db
