"""Server酱通知器"""

from __future__ import annotations

import logging

import requests

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
        try:
            url = f"https://sctapi.ftqq.com/{self._key}.send"
            data = {
                "title": f"【B站动态】{dynamic.upstream_name}",
                "desp": self.format_message(dynamic),
            }
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                return NotificationResult(success=True, message="Server酱通知发送成功")
            else:
                return NotificationResult(
                    success=False,
                    message=f"Server酱通知发送失败: {result.get('message')}",
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"Server酱通知发送异常: {e}",
            )
    
    def test(self) -> bool:
        """测试通知器"""
        try:
            url = f"https://sctapi.ftqq.com/{self._key}.send"
            data = {"title": "测试", "desp": "B站动态监控测试消息"}
            response = requests.post(url, data=data, timeout=10)
            return response.json().get("code") == 0
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
