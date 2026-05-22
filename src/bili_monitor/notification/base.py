"""通知模块基类"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..api.endpoints import DynamicInfo


@dataclass
class NotificationResult:
    """通知发送结果"""
    success: bool
    message: str
    timestamp: str = ""
    
    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class NotificationBase(ABC):
    """通知器基类"""
    
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("bili-monitor.notification")
    
    @abstractmethod
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        ...
    
    @abstractmethod
    def test(self) -> bool:
        """测试通知器是否正常工作"""
        ...
    
    def format_message(self, dynamic: DynamicInfo) -> str:
        """格式化动态信息为通知消息"""
        lines = []
        
        lines.append("📢 B站动态更新通知")
        lines.append("")
        lines.append(f"👤 UP主: {dynamic.upstream_name}")
        lines.append(f"📝 类型: {dynamic.dynamic_type}")
        lines.append("")
        
        if dynamic.content:
            content = dynamic.content[:500]
            if len(dynamic.content) > 500:
                content += "..."
            lines.append("📄 内容:")
            lines.append(content)
            lines.append("")
        
        if dynamic.video:
            lines.append(f"🎬 视频: {dynamic.video.title}")
            lines.append(f"   BVID: {dynamic.video.bvid}")
            lines.append("")
        
        if dynamic.images:
            lines.append(f"🖼️ 图片: {len(dynamic.images)} 张")
            lines.append("")
        
        lines.append(f"👍 点赞: {dynamic.stat.like:,}")
        lines.append(f"💬 评论: {dynamic.stat.comment:,}")
        lines.append(f"🔄 转发: {dynamic.stat.repost:,}")
        lines.append("")
        lines.append(f"🕐 时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M:%S') if dynamic.publish_time else '未知'}")
        lines.append(f"🔗 链接: https://www.bilibili.com/opus/{dynamic.dynamic_id}")
        
        return "\n".join(lines)
    
    def format_simple_message(self, dynamic: DynamicInfo) -> str:
        """格式化简化版通知消息"""
        type_emoji = {
            "图文": "🖼️",
            "投稿视频": "🎬",
            "专栏文章": "📝",
            "转发": "🔄",
            "纯文字": "💬",
        }.get(dynamic.dynamic_type.replace("充电专属-", ""), "📢")
        
        content_preview = dynamic.content[:100] if dynamic.content else ""
        if len(dynamic.content or "") > 100:
            content_preview += "..."
        
        return (
            f"{type_emoji} {dynamic.upstream_name} 发布了新动态\n"
            f"类型: {dynamic.dynamic_type}\n"
            f"内容: {content_preview}\n"
            f"链接: https://www.bilibili.com/opus/{dynamic.dynamic_id}"
        )
