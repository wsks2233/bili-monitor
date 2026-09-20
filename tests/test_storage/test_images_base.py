"""图片路径与 config 目录对齐"""

from __future__ import annotations

from pathlib import Path

from bili_monitor.config.models import DatabaseConfig
from bili_monitor.storage.database import Database


def test_database_images_base_explicit(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "bili_monitor.db"
    images = tmp_path / "images"
    db = Database(config=DatabaseConfig(path=str(db_path)), images_base=images)
    assert db.images_base == images
    db.close()


def test_database_images_base_fallback(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "bili_monitor.db"
    db = Database(config=DatabaseConfig(path=str(db_path)))
    assert db.images_base == tmp_path / "images"
    db.close()
