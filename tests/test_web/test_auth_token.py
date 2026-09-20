"""可选 API Token 鉴权"""

from __future__ import annotations

from pathlib import Path

import yaml

from bili_monitor.web.app import create_app


def _write_config(path: Path, auth_token: str = "") -> None:
    data = {
        "monitor": {"check_interval": 300, "cookie": ""},
        "upstreams": [],
        "logger": {"level": "INFO", "file": str(path.parent / "logs" / "t.log")},
        "database": {"path": str(path.parent / "data" / "t.db")},
        "web": {"host": "127.0.0.1", "port": 5000, "auth_token": auth_token},
        "notification": [],
    }
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


def test_no_token_allows_post(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, auth_token="")
    app = create_app(str(config_path))
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.post("/api/config", json={"monitor": {"check_interval": 60}})
    assert resp.status_code == 200


def test_token_required_for_write(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, auth_token="tok123")
    app = create_app(str(config_path))
    app.config["TESTING"] = True
    client = app.test_client()

    resp = client.post("/api/config", json={"monitor": {"check_interval": 60}})
    assert resp.status_code == 401

    resp = client.post(
        "/api/config",
        json={"monitor": {"check_interval": 60}},
        headers={"X-Auth-Token": "tok123"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/api/config",
        json={"monitor": {"check_interval": 90}},
        headers={"Authorization": "Bearer tok123"},
    )
    assert resp.status_code == 200

    # 读接口仍开放
    resp = client.get("/api/status")
    assert resp.status_code == 200

    # logs 受保护
    resp = client.get("/api/logs")
    assert resp.status_code == 401
    resp = client.get("/api/logs", headers={"X-Auth-Token": "tok123"})
    assert resp.status_code == 200
