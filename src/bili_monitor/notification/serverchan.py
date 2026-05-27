"""Server酱通知器"""

from __future__ import annotations

import logging

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class ServerChanNotifier(NotificationBase):
    """Server酱通知器"""

    def __init__(
        self,
        serverchan_key: str,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._key = serverchan_key

    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        url = f"https://sctapi.ftqq.com/{self._key}.send"
        data = {
            "title": f"【B站动态】{dynamic.upstream_name}",
            "desp": self.format_message(dynamic),
        }
        return self._request("POST", url, "code", 0, "Server酱", "Server酱", form_data=data)

    def test(self) -> bool:
        """测试通知器"""
        url = f"https://sctapi.ftqq.com/{self._key}.send"
        # Server酱 uses form data for test too, but _test_request uses json
        # so we override the test directly
        try:
            import requests as _req
            data = {"title": "测试", "desp": "B站动态监控测试消息"}
            response = _req.post(url, data=data, timeout=10)
            return response.json().get("code") == 0
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
