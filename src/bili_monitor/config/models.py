"""配置模型定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LoggerConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/bili-monitor.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/bili_monitor.db"


@dataclass(frozen=True)
class MonitorConfig:
    """监控配置"""
    check_interval: int = 300
    retry_times: int = 3
    retry_delay: int = 5
    cookie: str = ""


@dataclass(frozen=True)
class WebConfig:
    """Web服务配置"""
    host: str = "0.0.0.0"
    port: int = 5000


@dataclass(frozen=True)
class UpstreamConfig:
    """UP主配置"""
    uid: str
    name: str = ""
    face: str = ""
    fans: int = 0


@dataclass(frozen=True)
class NotificationConfig:
    """通知配置"""
    type: str
    webhook_url: str = ""
    secret: str = ""
    # Server酱
    serverchan_key: str = ""
    # PushPlus
    pushplus_token: str = ""
    # 邮件
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    sender: str = ""
    receivers: list[str] = field(default_factory=list)
    # Telegram
    bot_token: str = ""
    chat_id: str = ""


@dataclass(frozen=True)
class AppConfig:
    """应用总配置"""
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    upstreams: list[UpstreamConfig] = field(default_factory=list)
    logger: LoggerConfig = field(default_factory=LoggerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    web: WebConfig = field(default_factory=WebConfig)
    notification: list[NotificationConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        """从字典创建配置"""
        monitor_data = data.get("monitor", {})
        monitor = MonitorConfig(
            check_interval=int(monitor_data.get("check_interval", 300)),
            retry_times=int(monitor_data.get("retry_times", 3)),
            retry_delay=int(monitor_data.get("retry_delay", 5)),
            cookie=str(monitor_data.get("cookie", "")),
        )

        upstreams = []
        for item in data.get("upstreams", []):
            upstreams.append(UpstreamConfig(
                uid=str(item.get("uid", "")),
                name=str(item.get("name", "")),
                face=str(item.get("face", "")),
                fans=int(item.get("fans", 0)),
            ))

        logger_data = data.get("logger", {})
        logger = LoggerConfig(
            level=str(logger_data.get("level", "INFO")),
            file=str(logger_data.get("file", "logs/bili-monitor.log")),
            max_bytes=int(logger_data.get("max_bytes", 10 * 1024 * 1024)),
            backup_count=int(logger_data.get("backup_count", 5)),
        )

        db_data = data.get("database", {})
        database = DatabaseConfig(
            path=str(db_data.get("path", "data/bili_monitor.db")),
        )

        web_data = data.get("web", {})
        web = WebConfig(
            host=str(web_data.get("host", "0.0.0.0")),
            port=int(web_data.get("port", 5000)),
        )

        notifications = []
        for item in data.get("notification", []):
            notifications.append(NotificationConfig(
                type=str(item.get("type", "")),
                webhook_url=str(item.get("webhook_url", "")),
                secret=str(item.get("secret", "")),
                serverchan_key=str(item.get("serverchan_key", "")),
                pushplus_token=str(item.get("pushplus_token", "")),
                smtp_server=str(item.get("smtp_server", "")),
                smtp_port=int(item.get("smtp_port", 465)),
                smtp_user=str(item.get("smtp_user", "")),
                smtp_password=str(item.get("smtp_password", "")),
                sender=str(item.get("sender", "")),
                receivers=list(item.get("receivers", [])),
                bot_token=str(item.get("bot_token", "")),
                chat_id=str(item.get("chat_id", "")),
            ))

        return cls(
            monitor=monitor,
            upstreams=upstreams,
            logger=logger,
            database=database,
            web=web,
            notification=notifications,
        )
