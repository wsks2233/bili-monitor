"""钉钉通知器"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse

import requests

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
        try:
            url = self._sign_url()
            content = self.format_simple_message(dynamic)
            data = {"msgtype": "text", "text": {"content": content}}
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return NotificationResult(success=True, message="钉钉通知发送成功")
            else:
                return NotificationResult(
                    success=False,
                    message=f"钉钉通知发送失败: {result.get('errmsg')}",
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"钉钉通知发送异常: {e}",
            )
    
    def test(self) -> bool:
        """测试通知器"""
        try:
            url = self._sign_url()
            data = {"msgtype": "text", "text": {"content": "B站动态监控测试消息"}}
            response = requests.post(url, json=data, timeout=10)
            return response.json().get("errcode") == 0
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
