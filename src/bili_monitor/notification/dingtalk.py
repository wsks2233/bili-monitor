"""钉钉通知器"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class DingTalkNotifier(NotificationBase):
    """钉钉通知器"""

    def __init__(
        self,
        webhook_url: str,
        secret: str = "",
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._webhook_url = webhook_url
        self._secret = secret

    def _sign_url(self) -> str:
        """生成签名 URL"""
        if not self._secret:
            return self._webhook_url

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self._secret}"
        hmac_code = hmac.new(
            self._secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"{self._webhook_url}&timestamp={timestamp}&sign={sign}"

    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        content = self.format_simple_message(dynamic)
        data = {"msgtype": "text", "text": {"content": content}}
        return self._request("POST", self._sign_url(), "errcode", 0, "钉钉", "钉钉", json_data=data)

    def test(self) -> bool:
        """测试通知器"""
        data = {"msgtype": "text", "text": {"content": "B站动态监控测试消息"}}
        return self._test_request("POST", self._sign_url(), "errcode", 0, payload=data)
