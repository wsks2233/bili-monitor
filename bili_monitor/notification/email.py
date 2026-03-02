# -*- coding: utf-8 -*-
"""邮件通知器"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from .base import NotificationBase, NotificationResult
from ..core.models import DynamicInfo


class EmailNotifier(NotificationBase):
    """邮件通知器"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int = 465,
        smtp_user: str = "",
        smtp_password: str = "",
        sender: str = "",
        receivers: List[str] = None,
        use_ssl: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(logger)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender = sender or smtp_user
        self.receivers = receivers or []
        self.use_ssl = use_ssl
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        if not self.receivers:
            return NotificationResult(success=False, message="未配置邮件接收者")
        
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = f"【B站动态】{dynamic.upstream_name} 发布了新动态"
            message['From'] = self.sender
            message['To'] = ', '.join(self.receivers)
            
            message.attach(MIMEText(self.format_message(dynamic), 'plain', 'utf-8'))
            message.attach(MIMEText(self._format_html(dynamic), 'html', 'utf-8'))
            
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.sender, self.receivers, message.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.sender, self.receivers, message.as_string())
            
            return NotificationResult(success=True, message=f"邮件通知发送成功，接收者: {len(self.receivers)} 人")
        except Exception as e:
            return NotificationResult(success=False, message=f"邮件通知发送异常: {e}")
    
    def _format_html(self, dynamic: DynamicInfo) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: sans-serif; line-height: 1.6;">
            <h2>📢 B站动态更新通知</h2>
            <p>👤 UP主: <strong>{dynamic.upstream_name}</strong></p>
            <p>📝 类型: {dynamic.dynamic_type}</p>
            <p>🕐 时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <div style="white-space: pre-wrap;">{dynamic.content or ''}</div>
            <hr>
            <p>👍 {dynamic.stat.like:,} · 💬 {dynamic.stat.comment:,} · 🔄 {dynamic.stat.repost:,}</p>
            <p><a href="https://www.bilibili.com/opus/{dynamic.dynamic_id}">查看动态</a></p>
            <p style="color: #999; font-size: 12px;">B站UP主动态监控系统 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
    
    def test(self) -> bool:
        try:
            message = MIMEText("B站动态监控测试消息", 'plain', 'utf-8')
            message['Subject'] = "【测试】B站动态监控"
            message['From'] = self.sender
            message['To'] = self.receivers[0] if self.receivers else self.sender
            
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.sender, self.receivers[:1], message.as_string())
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.sender, self.receivers[:1], message.as_string())
            return True
        except Exception as e:
            self.logger.error(f"测试失败: {e}")
            return False
