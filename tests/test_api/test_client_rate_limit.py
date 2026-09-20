"""BiliHTTPClient 实例级限流与重试配置"""

from __future__ import annotations

from bili_monitor.api.client import BiliHTTPClient


def test_rate_limit_is_instance_level() -> None:
    c1 = BiliHTTPClient(rate_min=0.1, rate_max=0.2)
    c2 = BiliHTTPClient(rate_min=2.0, rate_max=4.0)
    assert c1.rate_limit_config["min_interval"] == 0.1
    assert c1.rate_limit_config["max_interval"] == 0.2
    assert c2.rate_limit_config["min_interval"] == 2.0
    assert c2.rate_limit_config["max_interval"] == 4.0
    # 类默认不被实例污染
    assert BiliHTTPClient.RATE_LIMIT_CONFIG["min_interval"] == 1.5
    assert BiliHTTPClient.RATE_LIMIT_CONFIG["max_interval"] == 3.0
    c1.close()
    c2.close()


def test_retry_times_from_config() -> None:
    c = BiliHTTPClient(retry_times=5, retry_delay=9.0)
    assert c.retry_times == 5
    assert c.rate_limit_config["retry_base"] == 9.0
    c.close()


def test_get_uses_instance_retry_times(monkeypatch) -> None:
    import requests as req

    c = BiliHTTPClient(retry_times=2, retry_delay=0.01)
    calls = {"n": 0}

    def boom(*_a, **_k):
        calls["n"] += 1
        raise req.RequestException("net down")

    monkeypatch.setattr(c._session, "get", boom)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    try:
        import pytest

        from bili_monitor.api.client import BiliAPIError

        with pytest.raises((BiliAPIError, req.RequestException)):
            c.get("https://example.com/x")
        assert calls["n"] == 2
    finally:
        c.close()


def test_config_hot_update_writes_instance_rate_limit() -> None:
    """热更新必须写 rate_limit_config，不得污染类属性"""
    from bili_monitor.api.client import BiliHTTPClient

    class _Mon:
        def __init__(self):
            self._client = BiliHTTPClient(rate_min=1.0, rate_max=2.0)
            self._running = True

    m = _Mon()
    # 模拟 config 路由热更新逻辑
    m._client.rate_limit_config["min_interval"] = 0.3
    m._client.rate_limit_config["max_interval"] = 0.6
    m._client.retry_times = 7
    assert m._client.rate_limit_config["min_interval"] == 0.3
    assert BiliHTTPClient.RATE_LIMIT_CONFIG["min_interval"] == 1.5
    assert m._client.retry_times == 7
    m._client.close()
