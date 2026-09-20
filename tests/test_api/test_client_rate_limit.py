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
