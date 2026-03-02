# -*- coding: utf-8 -*-
"""钉钉通知器"""

import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
from typing import Optional
import requests

from .base import NotificationBase, NotificationResult
from ..core.models import DynamicInfo


class DingTalkNotifier(NotificationBase):
    """钉钉通知器"""
    
    API_URL = "https://oapi.dingtalk.com/robot/send?access_token={token}"
    
    def __init__(self, webhook_url: str, secret: str = "", logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.webhook_url = webhook_url
        self.secret = secret
    
    def _sign_url(self) -> str:
        if not self.secret:
            return self.webhook_url
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(self.secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        try:
            url = self._sign_url()
            content = self.format_simple_message(dynamic)
            data = {"msgtype": "text", "text": {"content": content}}
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return NotificationResult(success=True, message="钉钉通知发送成功")
            else:
                return NotificationResult(success=False, message=f"钉钉通知发送失败: {result.get('errmsg')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"钉钉通知发送异常: {e}")
    
    def test(self) -> bool:
        try:
            url = self._sign_url()
            data = {"msgtype": "text", "text": {"content": "B站动态监控测试消息"}}
            response = requests.post(url, json=data, timeout=10)
            return response.json().get('errcode') == 0
        except Exception as e:
            self.logger.error(f"测试失败: {e}")
            return False
