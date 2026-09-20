"""Web 层：无 Monitor 时仍可读 SQLite；配置密钥掩码合并"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from bili_monitor.api.endpoints import DynamicInfo
from bili_monitor.config.loader import load_config
from bili_monitor.config.models import DatabaseConfig
from bili_monitor.storage.database import Database
from bili_monitor.web.app import create_app


def _write_config(path: Path, db_path: Path) -> None:
    data = {
        "monitor": {"check_interval": 300, "cookie": ""},
        "upstreams": [{"uid": "123", "name": "测试UP", "face": "", "fans": 0}],
        "logger": {"level": "INFO", "file": str(path.parent / "logs" / "t.log")},
        "database": {"path": str(db_path)},
        "web": {"host": "127.0.0.1", "port": 5000},
        "notification": [
            {
                "type": "wechat",
                "webhook_url": "https://example.com/hook-secret-value",
                "secret": "",
                "serverchan_key": "",
                "pushplus_token": "",
            },
            {
                "type": "dingtalk",
                "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=abc123secret",
                "secret": "dingtalk-sign-secret-value",
            },
            {
                "type": "email",
                "smtp_server": "smtp.example.com",
                "smtp_port": 465,
                "smtp_user": "a@b.com",
                "smtp_password": "email-password-secret",
                "sender": "a@b.com",
                "receivers": ["c@d.com"],
            },
        ],
    }
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def web_env(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    db_path = tmp_path / "data" / "bili_monitor.db"
    _write_config(config_path, db_path)
    db = Database(config=DatabaseConfig(path=str(db_path)))
    dyn = DynamicInfo(
        dynamic_id="d1",
        uid="123",
        upstream_name="测试UP",
        dynamic_type="图文",
        content="hello",
        publish_time=datetime(2026, 1, 1, 12, 0, 0),
        create_time=datetime(2026, 1, 1, 12, 0, 0),
    )
    db.save_dynamic(dyn)
    db.close()

    app = create_app(str(config_path))
    app.config["TESTING"] = True
    client = app.test_client()
    yield client, config_path, db_path


def test_dynamics_readable_without_monitor(web_env) -> None:
    client, _, _ = web_env
    resp = client.get("/api/dynamics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["dynamic_id"] == "d1"


def test_upstreams_readable_without_monitor(web_env) -> None:
    client, _, _ = web_env
    # 动态入库不会自动写 upstreams；插入空表应返回 []
    resp = client.get("/api/upstreams")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_status_readable_without_monitor(web_env) -> None:
    client, _, _ = web_env
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["running"] is False
    assert data["total_dynamics"] == 1


def test_config_get_masks_secrets(web_env) -> None:
    client, _, _ = web_env
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.get_json()
    notes = {n["type"]: n for n in data["notification"]}
    assert notes["wechat"]["webhook_url"] == "******"
    assert notes["dingtalk"]["secret"] == "******"
    assert notes["email"]["smtp_password"] == "******"


def test_config_post_preserves_masked_secrets(web_env) -> None:
    client, config_path, _ = web_env
    get_resp = client.get("/api/config")
    payload = get_resp.get_json()
    # 模拟 UI 原样回传掩码载荷
    post_resp = client.post("/api/config", json=payload)
    assert post_resp.status_code == 200
    reloaded = load_config(config_path)
    by_type = {n.type: n for n in reloaded.notification}
    assert by_type["wechat"].webhook_url == "https://example.com/hook-secret-value"
    assert by_type["dingtalk"].secret == "dingtalk-sign-secret-value"
    assert by_type["dingtalk"].webhook_url.endswith("access_token=abc123secret")
    assert by_type["email"].smtp_password == "email-password-secret"


def test_config_post_updates_when_plaintext(web_env) -> None:
    client, config_path, _ = web_env
    get_resp = client.get("/api/config")
    payload = get_resp.get_json()
    for n in payload["notification"]:
        if n["type"] == "wechat":
            n["webhook_url"] = "https://example.com/new-hook"
    post_resp = client.post("/api/config", json=payload)
    assert post_resp.status_code == 200
    reloaded = load_config(config_path)
    by_type = {n.type: n for n in reloaded.notification}
    assert by_type["wechat"].webhook_url == "https://example.com/new-hook"
    # 其他密钥仍保留
    assert by_type["dingtalk"].secret == "dingtalk-sign-secret-value"


def test_config_post_missing_notification_key_preserves(web_env) -> None:
    client, config_path, _ = web_env
    payload = {"monitor": {"check_interval": 120}}
    resp = client.post("/api/config", json=payload)
    assert resp.status_code == 200
    reloaded = load_config(config_path)
    by_type = {n.type: n for n in reloaded.notification}
    assert by_type["wechat"].webhook_url == "https://example.com/hook-secret-value"
    assert reloaded.monitor.check_interval == 120
    assert len(reloaded.upstreams) == 1


def test_config_post_clear_token(web_env) -> None:
    client, config_path, _ = web_env
    get_resp = client.get("/api/config")
    payload = get_resp.get_json()
    for n in payload["notification"]:
        if n["type"] == "dingtalk":
            n["secret"] = "__CLEAR__"
    resp = client.post("/api/config", json=payload)
    assert resp.status_code == 200
    reloaded = load_config(config_path)
    by_type = {n.type: n for n in reloaded.notification}
    assert by_type["dingtalk"].secret == ""
    assert by_type["dingtalk"].webhook_url.endswith("access_token=abc123secret")


def test_monitor_run_releases_lock_on_init_failure(tmp_path: Path, monkeypatch) -> None:
    """启动失败（组件初始化异常）后不得留下活 PID 锁文件"""
    from bili_monitor.config.models import AppConfig, MonitorConfig, UpstreamConfig
    from bili_monitor.monitor.runner import Monitor
    from bili_monitor.storage.lock import lock_path_for_database

    db_path = tmp_path / "data" / "bili_monitor.db"
    lock_path = lock_path_for_database(db_path)
    config = AppConfig(
        monitor=MonitorConfig(check_interval=1),
        upstreams=[UpstreamConfig(uid="1", name="x")],
    )
    config.database.path = str(db_path)

    def boom(*_a, **_k):
        raise RuntimeError("init failed")

    monkeypatch.setattr(Monitor, "_init_components", boom)
    monitor = Monitor(config, lock_path=str(lock_path))
    monitor.run()
    assert not lock_path.exists()
