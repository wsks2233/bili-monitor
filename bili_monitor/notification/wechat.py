# -*- coding: utf-8 -*-
"""
微信通知器

支持：
- 企业微信机器人
- Server酱
- PushPlus
"""

import logging
from typing import Optional
import requests

from .base import NotificationBase, NotificationResult
from ..core.models import DynamicInfo


class WeChatNotifier(NotificationBase):
    """微信通知器"""
    
    def __init__(
        self,
        webhook_url: str = "",
        serverchan_key: str = "",
        pushplus_token: str = "",
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(logger)
        self.webhook_url = webhook_url
        self.serverchan_key = serverchan_key
        self.pushplus_token = pushplus_token
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        if self.webhook_url:
            return self._send_enterprise_wechat(dynamic)
        elif self.serverchan_key:
            return self._send_serverchan(dynamic)
        elif self.pushplus_token:
            return self._send_pushplus(dynamic)
        else:
            return NotificationResult(success=False, message="未配置微信通知参数")
    
    def _send_enterprise_wechat(self, dynamic: DynamicInfo) -> NotificationResult:
        try:
            content = self.format_message(dynamic)
            data = {"msgtype": "text", "text": {"content": content}}
            response = requests.post(self.webhook_url, json=data, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return NotificationResult(success=True, message="企业微信通知发送成功")
            else:
                return NotificationResult(success=False, message=f"企业微信通知发送失败: {result.get('errmsg')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"企业微信通知发送异常: {e}")
    
    def _send_serverchan(self, dynamic: DynamicInfo) -> NotificationResult:
        try:
            url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
            data = {"title": f"【B站动态】{dynamic.upstream_name}", "desp": self.format_message(dynamic)}
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            if result.get('code') == 0:
                return NotificationResult(success=True, message="Server酱通知发送成功")
            else:
                return NotificationResult(success=False, message=f"Server酱通知发送失败: {result.get('message')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"Server酱通知发送异常: {e}")
    
    def _send_pushplus(self, dynamic: DynamicInfo) -> NotificationResult:
        try:
            url = "http://www.pushplus.plus/send"
            data = {"token": self.pushplus_token, "title": f"【B站动态】{dynamic.upstream_name}", "content": self.format_message(dynamic)}
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get('code') == 200:
                return NotificationResult(success=True, message="PushPlus通知发送成功")
            else:
                return NotificationResult(success=False, message=f"PushPlus通知发送失败: {result.get('msg')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"PushPlus通知发送异常: {e}")
    
    def test(self) -> bool:
        try:
            if self.webhook_url:
                data = {"msgtype": "text", "text": {"content": "B站动态监控测试消息"}}
                response = requests.post(self.webhook_url, json=data, timeout=10)
                return response.json().get('errcode') == 0
            return False
        except Exception as e:
            self.logger.error(f"测试失败: {e}")
            return False
