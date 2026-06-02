"""配置模型定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoggerConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/bili-monitor.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/bili_monitor.db"


@dataclass
class MonitorConfig:
    """监控配置"""
    check_interval: int = 300
    retry_times: int = 3
    retry_delay: int = 5
    cookie: str = ""
    # 随机抖动配置（秒）
    request_min: float = 1.5    # API请求最小间隔
    request_max: float = 3.0    # API请求最大间隔
    upstream_min: float = 2.0   # 检查UP主最小间隔
    upstream_max: float = 5.0   # 检查UP主最大间隔
    error_min: float = 3.0      # 错误重试最小间隔
    error_max: float = 6.0      # 错误重试最大间隔

    def validate(self) -> list[str]:
        """校验配置，返回警告列表"""
        warnings = []
        # min <= max
        if self.request_min > self.request_max:
            warnings.append("API请求最小间隔不能大于最大间隔")
        if self.upstream_min > self.upstream_max:
            warnings.append("UP主检查最小间隔不能大于最大间隔")
        if self.error_min > self.error_max:
            warnings.append("错误重试最小间隔不能大于最大间隔")
        # 上限不超过 check_interval
        if self.upstream_max > self.check_interval:
            warnings.append(f"UP主检查最大间隔({self.upstream_max}s)超过检查间隔({self.check_interval}s)，已自动修正")
            self.upstream_max = self.check_interval
            if self.upstream_min > self.upstream_max:
                self.upstream_min = self.upstream_max
        if self.error_max > self.check_interval:
            warnings.append(f"错误重试最大间隔({self.error_max}s)超过检查间隔({self.check_interval}s)，已自动修正")
            self.error_max = self.check_interval
            if self.error_min > self.error_max:
                self.error_min = self.error_max
        return warnings


@dataclass
class WebConfig:
    """Web服务配置"""
    host: str = "0.0.0.0"
    port: int = 5000


@dataclass
class UpstreamConfig:
    """UP主配置"""
    uid: str
    name: str = ""
    face: str = ""
    fans: int = 0


@dataclass
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


@dataclass
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
            request_min=float(monitor_data.get("request_min", 1.5)),
            request_max=float(monitor_data.get("request_max", 3.0)),
            upstream_min=float(monitor_data.get("upstream_min", 2.0)),
            upstream_max=float(monitor_data.get("upstream_max", 5.0)),
            error_min=float(monitor_data.get("error_min", 3.0)),
            error_max=float(monitor_data.get("error_max", 6.0)),
        )

        upstreams = []
        for item in data.get("upstreams", []):
            upstreams.append(UpstreamConfig(
                uid=str(item.get("uid", "")),
                name=str(item.get("name", "")),
                face=str(item.get("face") or ""),
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
