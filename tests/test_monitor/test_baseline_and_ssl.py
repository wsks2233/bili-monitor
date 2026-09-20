"""P1：首跑 baseline 与 email.use_ssl"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from bili_monitor.api.endpoints import DynamicInfo
from bili_monitor.config.models import (
    AppConfig,
    MonitorConfig,
    NotificationConfig,
    UpstreamConfig,
)
from bili_monitor.monitor.runner import Monitor
from bili_monitor.notification import create_notifier
from bili_monitor.notification.email import EmailNotifier
from bili_monitor.storage.database import Database
from bili_monitor.config.models import DatabaseConfig


class _FakeAPI:
    def __init__(self, dynamics: list[DynamicInfo]) -> None:
        self._dynamics = dynamics

    def get_user_dynamics(self, uid: str) -> list[DynamicInfo]:
        return self._dynamics


def _dyn(did: str) -> DynamicInfo:
    return DynamicInfo(dynamic_id=did, uid="1", upstream_name="u", dynamic_type="图文", content="c")


def test_baseline_seed_skips_notification(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "t.db"
    db = Database(config=DatabaseConfig(path=str(db_path)))
    config = AppConfig(
        monitor=MonitorConfig(seed_baseline=True, notify_on_seed=False, check_interval=1),
        upstreams=[UpstreamConfig(uid="1", name="u")],
    )
    sent: list = []

    class _N:
        def send(self, dynamic):
            sent.append(dynamic.dynamic_id)
            from bili_monitor.notification.base import NotificationResult
            return NotificationResult(success=True, message="ok")

    monitor = Monitor(config)
    monitor._db = db
    monitor._api = _FakeAPI([_dyn("d1"), _dyn("d2")])
    monitor._notifiers = [_N()]
    monitor._image_downloader = None
    monitor._check_upstream(config.upstreams[0])
    assert sent == []
    ids = db.get_processed_ids("1")
    assert ids == {"d1", "d2"}
    db.close()


def test_baseline_disabled_notifies(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "t.db"
    db = Database(config=DatabaseConfig(path=str(db_path)))
    config = AppConfig(
        monitor=MonitorConfig(seed_baseline=False, check_interval=1),
        upstreams=[UpstreamConfig(uid="1", name="u")],
    )
    sent: list = []

    class _N:
        def send(self, dynamic):
            sent.append(dynamic.dynamic_id)
            from bili_monitor.notification.base import NotificationResult
            return NotificationResult(success=True, message="ok")

    monitor = Monitor(config)
    monitor._db = db
    monitor._api = _FakeAPI([_dyn("d1")])
    monitor._notifiers = [_N()]
    monitor._image_downloader = None
    monitor._check_upstream(config.upstreams[0])
    assert sent == ["d1"]
    db.close()


def test_create_notifier_email_use_ssl_false() -> None:
    n = create_notifier(
        "email",
        smtp_server="smtp.example.com",
        smtp_port=465,
        smtp_user="a@b.com",
        smtp_password="x",
        sender="a@b.com",
        receivers=["c@d.com"],
        use_ssl=False,
    )
    assert isinstance(n, EmailNotifier)
    assert n._use_ssl is False


def test_notification_config_use_ssl_default() -> None:
    n = NotificationConfig(type="email")
    assert n.use_ssl is True
