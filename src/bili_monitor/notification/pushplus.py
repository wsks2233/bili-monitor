"""PushPlus通知器"""

from __future__ import annotations

import logging

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class PushPlusNotifier(NotificationBase):
    """PushPlus通知器"""

    def __init__(
        self,
        pushplus_token: str,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._token = pushplus_token

    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        data = {
            "token": self._token,
            "title": f"【B站动态】{dynamic.upstream_name}",
            "content": self.format_message(dynamic),
        }
        return self._request("POST", "http://www.pushplus.plus/send", "code", 200, "PushPlus", "PushPlus", json_data=data)

    def test(self) -> bool:
        """测试通知器"""
        data = {"token": self._token, "title": "测试", "content": "B站动态监控测试消息"}
        return self._test_request("POST", "http://www.pushplus.plus/send", "code", 200, payload=data)
