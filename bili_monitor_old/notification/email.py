# -*- coding: utf-8 -*-
"""邮件通知器"""

import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
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
            message = MIMEMultipart('related')
            message['Subject'] = f"【B站】{dynamic.upstream_name} 新动态"
            message['From'] = self.sender
            message['To'] = ', '.join(self.receivers)
            
            # 创建alternative部分
            msg_alternative = MIMEMultipart('alternative')
            message.attach(msg_alternative)
            
            msg_alternative.attach(MIMEText(self._format_simple_text(dynamic), 'plain', 'utf-8'))
            
            # 处理图片
            image_attachments = []
            if dynamic.images:
                for i, image in enumerate(dynamic.images[:3]):  # 最多发送3张图片
                    try:
                        response = requests.get(image.url, timeout=10)
                        response.raise_for_status()
                        img_data = response.content
                        img = MIMEImage(img_data)
                        img.add_header('Content-ID', f'<image{i}>')
                        message.attach(img)
                        image_attachments.append(f'<image{i}>')
                    except Exception as e:
                        self.logger.warning(f"下载图片失败: {e}")
            
            # 添加HTML内容
            msg_alternative.attach(MIMEText(self._format_simple_html(dynamic, image_attachments), 'html', 'utf-8'))
            
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
    
    def _format_simple_text(self, dynamic: DynamicInfo) -> str:
        """简洁的纯文本格式"""
        lines = []
        lines.append(f"{dynamic.upstream_name} 发布了新动态")
        lines.append(f"类型: {dynamic.dynamic_type}")
        lines.append(f"时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        if dynamic.content:
            content = dynamic.content[:200]  # 限制内容长度
            if len(dynamic.content) > 200:
                content += "..."
            lines.append(content)
            lines.append("")
        
        lines.append(f"点赞: {dynamic.stat.like:,} | 评论: {dynamic.stat.comment:,} | 转发: {dynamic.stat.repost:,}")
        lines.append(f"链接: https://www.bilibili.com/opus/{dynamic.dynamic_id}")
        
        return "\n".join(lines)
    
    def _format_simple_html(self, dynamic: DynamicInfo, image_attachments: List[str] = None) -> str:
        """简洁的HTML格式"""
        content_preview = dynamic.content[:300] if dynamic.content else ""
        if len(dynamic.content or "") > 300:
            content_preview += "..."
        
        # 构建图片HTML
        images_html = ""
        if image_attachments:
            images_html = '<div style="margin-bottom: 15px;">' + ''.join([f'<img src="cid:{img_id[1:-1]}" style="max-width: 100%; height: auto; margin-bottom: 10px; border-radius: 4px;" alt="动态图片">' for img_id in image_attachments]) + '</div>'
        
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
            {images_html}
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
