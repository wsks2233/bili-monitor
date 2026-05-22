"""PushPlus通知器"""

from __future__ import annotations

import logging

import requests

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
        try:
            url = "http://www.pushplus.plus/send"
            data = {
                "token": self._token,
                "title": f"【B站动态】{dynamic.upstream_name}",
                "content": self.format_message(dynamic),
            }
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 200:
                return NotificationResult(success=True, message="PushPlus通知发送成功")
            else:
                return NotificationResult(
                    success=False,
                    message=f"PushPlus通知发送失败: {result.get('msg')}",
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"PushPlus通知发送异常: {e}",
            )
    
    def test(self) -> bool:
        """测试通知器"""
        try:
            url = "http://www.pushplus.plus/send"
            data = {
                "token": self._token,
                "title": "测试",
                "content": "B站动态监控测试消息",
            }
            response = requests.post(url, json=data, timeout=10)
            return response.json().get("code") == 200
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
