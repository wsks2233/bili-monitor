"""登录写 Cookie 时保留 Monitor 抖动字段"""

from __future__ import annotations

from pathlib import Path

import yaml

from bili_monitor.config.loader import load_config, save_config
from bili_monitor.config.models import AppConfig, MonitorConfig, UpstreamConfig


def test_monitor_config_fields_survive_cookie_update(tmp_path: Path) -> None:
    config = AppConfig(
        monitor=MonitorConfig(
            check_interval=120,
            request_min=0.5,
            request_max=1.5,
            upstream_min=1.0,
            upstream_max=2.0,
            error_min=3.0,
            error_max=4.0,
            cookie="old_cookie_value_long_enough_xxx",
        ),
        upstreams=[UpstreamConfig(uid="1", name="u")],
    )
    path = tmp_path / "config.yaml"
    save_config(config, path)

    # 模拟 login 路径：原地改 cookie
    loaded = load_config(path)
    loaded.monitor.cookie = "new_cookie_value_long_enough_yyy"
    save_config(loaded, path)

    again = load_config(path)
    assert again.monitor.cookie == "new_cookie_value_long_enough_yyy"
    assert again.monitor.check_interval == 120
    assert again.monitor.request_min == 0.5
    assert again.monitor.request_max == 1.5
    assert again.monitor.upstream_min == 1.0
    assert again.monitor.upstream_max == 2.0
    assert again.monitor.error_min == 3.0
    assert again.monitor.error_max == 4.0


def test_web_auth_token_in_yaml_roundtrip(tmp_path: Path) -> None:
    config = AppConfig()
    config.web.auth_token = "secret-token-abc"
    path = tmp_path / "config.yaml"
    save_config(config, path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["web"]["auth_token"] == "secret-token-abc"
    loaded = load_config(path)
    assert loaded.web.auth_token == "secret-token-abc"
