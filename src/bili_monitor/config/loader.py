"""配置加载器"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import AppConfig


class ConfigError(Exception):
    """配置错误"""


def load_config(config_path: str | Path = "config.yaml") -> AppConfig:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        AppConfig: 应用配置
        
    Raises:
        ConfigError: 配置文件不存在或格式错误
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigError(f"配置文件 {path} 不存在")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"配置文件格式错误: {e}")
    
    if not data:
        raise ConfigError("配置文件为空")
    
    return AppConfig.from_dict(data)


def save_config(config: AppConfig, config_path: str | Path = "config.yaml") -> None:
    """保存配置到文件
    
    Args:
        config: 应用配置
        config_path: 配置文件路径
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "monitor": {
            "check_interval": config.monitor.check_interval,
            "retry_times": config.monitor.retry_times,
            "retry_delay": config.monitor.retry_delay,
            "cookie": config.monitor.cookie,
        },
        "upstreams": [
            {
                "uid": u.uid,
                "name": u.name,
                "face": u.face,
                "fans": u.fans,
            }
            for u in config.upstreams
        ],
        "logger": {
            "level": config.logger.level,
            "file": config.logger.file,
            "max_bytes": config.logger.max_bytes,
            "backup_count": config.logger.backup_count,
        },
        "database": {
            "path": config.database.path,
        },
        "web": {
            "host": config.web.host,
            "port": config.web.port,
        },
        "notification": [
            {
                "type": n.type,
                "webhook_url": n.webhook_url,
                "secret": n.secret,
                "serverchan_key": n.serverchan_key,
                "pushplus_token": n.pushplus_token,
                "smtp_server": n.smtp_server,
                "smtp_port": n.smtp_port,
                "smtp_user": n.smtp_user,
                "smtp_password": n.smtp_password,
                "sender": n.sender,
                "receivers": n.receivers,
                "bot_token": n.bot_token,
                "chat_id": n.chat_id,
            }
            for n in config.notification
        ],
    }
    
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
