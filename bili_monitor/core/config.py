# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import yaml


@dataclass
class LoggerConfig:
    level: str = "INFO"
    file: str = "logs/bili-monitor.log"
    max_bytes: int = 10485760
    backup_count: int = 5


@dataclass
class DatabaseConfig:
    path: str = "data/bili_monitor.db"


@dataclass
class MonitorConfig:
    check_interval: int = 300
    retry_times: int = 3
    retry_delay: int = 5
    cookie: str = ""


@dataclass
class UpstreamConfig:
    uid: str
    name: str = ""
    face: str = ""
    fans: int = 0


@dataclass
class Config:
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    upstreams: List[UpstreamConfig] = field(default_factory=list)
    logger: LoggerConfig = field(default_factory=LoggerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    notification: List[Dict[str, Any]] = field(default_factory=list)


def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        raise ValueError("配置文件为空")
    
    monitor_config = MonitorConfig(
        check_interval=data.get('monitor', {}).get('check_interval', 300),
        retry_times=data.get('monitor', {}).get('retry_times', 3),
        retry_delay=data.get('monitor', {}).get('retry_delay', 5),
        cookie=data.get('monitor', {}).get('cookie', ''),
    )
    
    upstreams = []
    for item in data.get('upstreams', []):
        upstreams.append(UpstreamConfig(
            uid=str(item.get('uid', '')),
            name=item.get('name', ''),
            face=item.get('face', ''),
            fans=item.get('fans', 0),
        ))
    
    logger_config = LoggerConfig(
        level=data.get('logger', {}).get('level', 'INFO'),
        file=data.get('logger', {}).get('file', 'logs/bili-monitor.log'),
        max_bytes=data.get('logger', {}).get('max_bytes', 10485760),
        backup_count=data.get('logger', {}).get('backup_count', 5),
    )
    
    db_data = data.get('database', {})
    database_config = DatabaseConfig(
        path=db_data.get('path', 'data/bili_monitor.db'),
    )
    
    notification = data.get('notification', [])
    
    return Config(
        monitor=monitor_config,
        upstreams=upstreams,
        logger=logger_config,
        database=database_config,
        notification=notification,
    )
