"""企业微信通知器"""

from __future__ import annotations

import logging
from typing import Any

import requests

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class WeChatNotifier(NotificationBase):
    """企业微信机器人通知器"""
    
    def __init__(
        self,
        webhook_url: str,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._webhook_url = webhook_url
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        try:
            # 根据动态类型生成正确的链接
            if dynamic.dynamic_type in ["图文", "转发", "充电专属-图文"]:
                url = f"https://t.bilibili.com/{dynamic.dynamic_id}"
            else:
                url = f"https://www.bilibili.com/opus/{dynamic.dynamic_id}"
            
            # 构建文本消息内容
            content_lines = [
                f"【{dynamic.upstream_name} 发布了新动态】",
                f"类型: {dynamic.dynamic_type}",
                f"时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}",
            ]
            
            if dynamic.content:
                content_preview = dynamic.content[:200]
                if len(dynamic.content) > 200:
                    content_preview += "..."
                content_lines.append(f"内容: {content_preview}")
            
            content_lines.append(f"链接: {url}")
            
            data = {
                "msgtype": "text",
                "text": {"content": "\n".join(content_lines)},
            }
            
            response = requests.post(self._webhook_url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return NotificationResult(success=True, message="企业微信通知发送成功")
            else:
                return NotificationResult(
                    success=False,
                    message=f"企业微信通知发送失败: {result.get('errmsg')}",
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"企业微信通知发送异常: {e}",
            )
    
    def test(self) -> bool:
        """测试通知器"""
        try:
            data = {
                "msgtype": "text",
                "text": {"content": "B站动态监控测试消息"},
            }
            response = requests.post(self._webhook_url, json=data, timeout=10)
            return response.json().get("errcode") == 0
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
