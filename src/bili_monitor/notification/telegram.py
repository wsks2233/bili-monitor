"""Telegram通知器"""

from __future__ import annotations

import logging

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class TelegramNotifier(NotificationBase):
    """Telegram通知器"""

    API_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        parse_mode: str = "Markdown",
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._parse_mode = parse_mode

    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        url = self.API_URL.format(token=self._bot_token, method="sendMessage")
        data = {
            "chat_id": self._chat_id,
            "text": self._format_markdown(dynamic),
            "parse_mode": self._parse_mode,
            "disable_web_page_preview": False,
        }
        return self._request("POST", url, "ok", True, "Telegram", "Telegram", json_data=data, timeout=30)

    def _format_markdown(self, dynamic: DynamicInfo) -> str:
        """格式化 Markdown"""
        lines = [
            "📢 *B站动态更新通知*",
            "",
            f"👤 UP主: {self._escape_markdown(dynamic.upstream_name)}",
            f"📝 类型: {dynamic.dynamic_type}",
            f"🕐 时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if dynamic.content:
            content = dynamic.content[:1000]
            if len(dynamic.content) > 1000:
                content += "..."
            lines.append(f"📄 内容:\n```\n{content}\n```")
            lines.append("")

        if dynamic.video:
            lines.append(f"🎬 *视频*: {self._escape_markdown(dynamic.video.title)}")
            lines.append(f"   BVID: `{dynamic.video.bvid}`")
            lines.append("")

        if dynamic.images:
            lines.append(f"🖼️ 图片: {len(dynamic.images)} 张")
            lines.append("")

        lines.extend([
            f"👍 点赞: {dynamic.stat.like:,}",
            f"💬 评论: {dynamic.stat.comment:,}",
            f"🔄 转发: {dynamic.stat.repost:,}",
            "",
            f"🔗 [查看动态](https://www.bilibili.com/opus/{dynamic.dynamic_id})",
        ])

        return "\n".join(lines)

    def _escape_markdown(self, text: str) -> str:
        """转义 Markdown 特殊字符"""
        for char in ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]:
            text = text.replace(char, f"\\{char}")
        return text

    def test(self) -> bool:
        """测试通知器"""
        url = self.API_URL.format(token=self._bot_token, method="sendMessage")
        data = {"chat_id": self._chat_id, "text": "B站动态监控测试消息"}
        return self._test_request("POST", url, "ok", True, payload=data)
