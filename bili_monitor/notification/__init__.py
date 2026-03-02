# -*- coding: utf-8 -*-
"""
通知模块

包含：
- base: 通知基类
- wechat: 微信通知（企业微信、Server酱等）
- dingtalk: 钉钉通知
- email: 邮件通知
- telegram: Telegram通知

使用方法：
```python
from bili_monitor.notification import create_notifier

# 创建通知器
notifier = create_notifier('wechat', webhook_url='...')
notifier = create_notifier('dingtalk', webhook_url='...')
notifier = create_notifier('email', smtp_server='...')

# 发送通知
notifier.send(dynamic)
```
"""

from .base import NotificationBase, NotificationResult

__all__ = [
    'NotificationBase',
    'NotificationResult',
    'create_notifier',
]

def create_notifier(notifier_type: str, **kwargs):
    """
    创建通知器
    
    Args:
        notifier_type: 通知类型 (wechat, dingtalk, email, telegram)
        **kwargs: 通知器配置
        
    Returns:
        NotificationBase: 通知器实例
    """
    notifier_type = notifier_type.lower()
    
    if notifier_type == 'wechat':
        from .wechat import WeChatNotifier
        return WeChatNotifier(**kwargs)
    elif notifier_type == 'dingtalk':
        from .dingtalk import DingTalkNotifier
        return DingTalkNotifier(**kwargs)
    elif notifier_type == 'email':
        from .email import EmailNotifier
        return EmailNotifier(**kwargs)
    elif notifier_type == 'telegram':
        from .telegram import TelegramNotifier
        return TelegramNotifier(**kwargs)
    else:
        raise ValueError(f"不支持的通知类型: {notifier_type}")
