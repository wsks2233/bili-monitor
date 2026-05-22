"""邮件通知器"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import requests

from ..api.endpoints import DynamicInfo
from .base import NotificationBase, NotificationResult


class EmailNotifier(NotificationBase):
    """邮件通知器"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int = 465,
        smtp_user: str = "",
        smtp_password: str = "",
        sender: str = "",
        receivers: list[str] | None = None,
        use_ssl: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(logger)
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._sender = sender or smtp_user
        self._receivers = receivers or []
        self._use_ssl = use_ssl
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        """发送通知"""
        if not self._receivers:
            return NotificationResult(success=False, message="未配置邮件接收者")
        
        try:
            message = MIMEMultipart("related")
            message["Subject"] = f"【B站】{dynamic.upstream_name} 新动态"
            message["From"] = self._sender
            message["To"] = ", ".join(self._receivers)
            
            # 创建 alternative 部分
            msg_alternative = MIMEMultipart("alternative")
            message.attach(msg_alternative)
            
            # 纯文本内容
            msg_alternative.attach(
                MIMEText(self._format_text(dynamic), "plain", "utf-8")
            )
            
            # HTML 内容
            msg_alternative.attach(
                MIMEText(self._format_html(dynamic), "html", "utf-8")
            )
            
            # 发送邮件
            if self._use_ssl:
                with smtplib.SMTP_SSL(self._smtp_server, self._smtp_port) as server:
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._sender, self._receivers, message.as_string())
            else:
                with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
                    server.starttls()
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._sender, self._receivers, message.as_string())
            
            return NotificationResult(
                success=True,
                message=f"邮件通知发送成功，接收者: {len(self._receivers)} 人",
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                message=f"邮件通知发送异常: {e}",
            )
    
    def _format_text(self, dynamic: DynamicInfo) -> str:
        """格式化纯文本"""
        lines = [
            f"{dynamic.upstream_name} 发布了新动态",
            f"类型: {dynamic.dynamic_type}",
            f"时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        
        if dynamic.content:
            content = dynamic.content[:200]
            if len(dynamic.content) > 200:
                content += "..."
            lines.append(content)
            lines.append("")
        
        lines.append(
            f"点赞: {dynamic.stat.like:,} | "
            f"评论: {dynamic.stat.comment:,} | "
            f"转发: {dynamic.stat.repost:,}"
        )
        lines.append(f"链接: https://www.bilibili.com/opus/{dynamic.dynamic_id}")
        
        return "\n".join(lines)
    
    def _format_html(self, dynamic: DynamicInfo) -> str:
        """格式化 HTML"""
        content_preview = dynamic.content[:300] if dynamic.content else ""
        if len(dynamic.content or "") > 300:
            content_preview += "..."
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <h3 style="margin-bottom: 10px;">{dynamic.upstream_name} 发布了新动态</h3>
            <div style="font-size: 14px; color: #666; margin-bottom: 15px;">
                <span style="margin-right: 15px;">类型: {dynamic.dynamic_type}</span>
                <span>时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}</span>
            </div>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; margin-bottom: 15px; white-space: pre-wrap;">
                {content_preview or '无内容'}
            </div>
            <div style="margin-bottom: 15px; font-size: 14px;">
                👍 {dynamic.stat.like:,} · 💬 {dynamic.stat.comment:,} · 🔄 {dynamic.stat.repost:,}
            </div>
            <div style="margin-bottom: 20px;">
                <a href="https://www.bilibili.com/opus/{dynamic.dynamic_id}" style="
                    display: inline-block;
                    padding: 8px 16px;
                    background: #00a1d6;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 14px;
                ">查看动态</a>
            </div>
            <div style="font-size: 12px; color: #999;">
                B站动态监控系统
            </div>
        </body>
        </html>
        """
    
    def test(self) -> bool:
        """测试通知器"""
        try:
            message = MIMEText("B站动态监控测试消息", "plain", "utf-8")
            message["Subject"] = "【测试】B站动态监控"
            message["From"] = self._sender
            message["To"] = self._receivers[0] if self._receivers else self._sender
            
            if self._use_ssl:
                with smtplib.SMTP_SSL(self._smtp_server, self._smtp_port) as server:
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._sender, self._receivers[:1], message.as_string())
            else:
                with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
                    server.starttls()
                    server.login(self._smtp_user, self._smtp_password)
                    server.sendmail(self._sender, self._receivers[:1], message.as_string())
            return True
        except Exception as e:
            self._logger.error(f"测试失败: {e}")
            return False
