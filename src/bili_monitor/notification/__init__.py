"""通知模块"""

from __future__ import annotations

import logging
from typing import Any

from .base import NotificationBase, NotificationResult
from .dingtalk import DingTalkNotifier
from .email import EmailNotifier
from .pushplus import PushPlusNotifier
from .serverchan import ServerChanNotifier
from .telegram import TelegramNotifier
from .wechat import WeChatNotifier


def create_notifier(
    notifier_type: str,
    logger: logging.Logger | None = None,
    **kwargs: Any,
) -> NotificationBase:
    """创建通知器工厂函数
    
    Args:
        notifier_type: 通知类型 (wechat, serverchan, pushplus, dingtalk, email, telegram)
        logger: 日志记录器
        **kwargs: 通知器配置
        
    Returns:
        通知器实例
    """
    notifier_type = notifier_type.lower()

    # 过滤掉空字符串值，避免其他类型的字段干扰
    kwargs = {k: v for k, v in kwargs.items() if v != '' and v is not None}

    if notifier_type == "wechat":
        return WeChatNotifier(logger=logger, **kwargs)
    elif notifier_type == "serverchan":
        return ServerChanNotifier(logger=logger, **kwargs)
    elif notifier_type == "pushplus":
        return PushPlusNotifier(logger=logger, **kwargs)
    elif notifier_type == "dingtalk":
        return DingTalkNotifier(logger=logger, **kwargs)
    elif notifier_type == "email":
        return EmailNotifier(logger=logger, **kwargs)
    elif notifier_type == "telegram":
        return TelegramNotifier(logger=logger, **kwargs)
    else:
        raise ValueError(f"不支持的通知类型: {notifier_type}")


__all__ = [
    "DingTalkNotifier",
    "EmailNotifier",
    "NotificationBase",
    "NotificationResult",
    "PushPlusNotifier",
    "ServerChanNotifier",
    "TelegramNotifier",
    "WeChatNotifier",
    "create_notifier",
]
