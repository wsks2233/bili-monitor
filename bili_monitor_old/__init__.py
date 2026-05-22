# -*- coding: utf-8 -*-
"""
B站UP主动态监控系统

模块结构：
- core/       : 核心模块（配置、日志、模型）
- api/        : API模块（B站API、Cookie管理）
- storage/    : 存储模块（数据库）
- notification/: 通知模块（微信、钉钉、邮件等）
"""

from .monitor import Monitor
from .core.config import load_config, Config
from .core.logger import setup_logger
from .core.models import DynamicInfo, UpstreamInfo, ImageInfo, VideoInfo, StatInfo

__version__ = '1.0.0'
__all__ = [
    'Monitor',
    'load_config',
    'Config',
    'setup_logger',
    'DynamicInfo',
    'UpstreamInfo',
    'ImageInfo',
    'VideoInfo',
    'StatInfo',
]
