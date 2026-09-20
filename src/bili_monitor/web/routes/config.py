"""配置相关路由"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from ...config.loader import load_config, save_config
from ...config.models import (
    AppConfig,
    DatabaseConfig,
    LoggerConfig,
    MonitorConfig,
    NotificationConfig,
    UpstreamConfig,
    WebConfig,
)

logger = logging.getLogger("bili-monitor.web")

config_bp = Blueprint("config", __name__)


def _mask_secret(value: str) -> str:
    """敏感字段统一掩码为固定占位，避免半截泄露"""
    return "******" if value else ""


def _is_masked(value: Any) -> bool:
    """判断请求值是否为掩码占位或空（应保留磁盘现值）"""
    if value is None:
        return True
    s = str(value)
    return s == "" or s == "******" or s.endswith("...") or "..." in s


def _keep_or_new(new_value: Any, old_value: str) -> str:
    if new_value is None:
        return old_value or ""
    s = str(new_value)
    if s == "__CLEAR__":
        return ""
    if _is_masked(s):
        return old_value or ""
    return s


def _merge_notification(raw: dict[str, Any], existing: NotificationConfig | None) -> NotificationConfig:
    """合并通知配置：掩码/空值保留 existing，明文覆盖"""
    base = existing or NotificationConfig(type=str(raw.get("type", "")))
    n_type = str(raw.get("type") or base.type or "")
    merged = NotificationConfig(type=n_type)
    merged.webhook_url = _keep_or_new(raw.get("webhook_url", ""), base.webhook_url)
    merged.secret = _keep_or_new(raw.get("secret", ""), base.secret)
    merged.serverchan_key = _keep_or_new(raw.get("serverchan_key", ""), base.serverchan_key)
    merged.pushplus_token = _keep_or_new(raw.get("pushplus_token", ""), base.pushplus_token)
    merged.smtp_server = _keep_or_new(raw.get("smtp_server", ""), base.smtp_server)
    if raw.get("smtp_port") not in (None, ""):
        try:
            merged.smtp_port = int(raw.get("smtp_port"))
        except (TypeError, ValueError):
            merged.smtp_port = base.smtp_port
    else:
        merged.smtp_port = base.smtp_port
    merged.smtp_user = _keep_or_new(raw.get("smtp_user", ""), base.smtp_user)
    merged.smtp_password = _keep_or_new(raw.get("smtp_password", ""), base.smtp_password)
    merged.sender = _keep_or_new(raw.get("sender", ""), base.sender)
    receivers = raw.get("receivers", None)
    if receivers is None or _is_masked(receivers):
        merged.receivers = list(base.receivers or [])
    elif isinstance(receivers, list):
        merged.receivers = [str(r) for r in receivers]
    else:
        merged.receivers = list(base.receivers or [])
    merged.bot_token = _keep_or_new(raw.get("bot_token", ""), base.bot_token)
    merged.chat_id = _keep_or_new(raw.get("chat_id", ""), base.chat_id)
    return merged


def _find_existing_notification(
    current_list: list[NotificationConfig],
    n_type: str,
    index: int,
) -> NotificationConfig | None:
    if n_type:
        for item in current_list:
            if item.type == n_type:
                return item
    if 0 <= index < len(current_list):
        return current_list[index]
    return None


@config_bp.route("/api/config", methods=["GET"])
def get_config() -> Any:
    """获取配置"""
    try:
        config_path = current_app.config["CONFIG_PATH"]
        config = load_config(config_path)

        # 构建响应
        notification_list = []
        for n in config.notification:
            notification_list.append({
                "type": n.type,
                "webhook_url": _mask_secret(n.webhook_url),
                "secret": _mask_secret(n.secret),
                "serverchan_key": _mask_secret(n.serverchan_key),
                "pushplus_token": _mask_secret(n.pushplus_token),
                "smtp_server": n.smtp_server,
                "smtp_port": n.smtp_port,
                "smtp_user": n.smtp_user,
                "smtp_password": _mask_secret(n.smtp_password),
                "sender": n.sender,
                "receivers": n.receivers,
                "bot_token": _mask_secret(n.bot_token),
                "chat_id": n.chat_id,
            })

        upstreams = []
        for u in config.upstreams:
            upstreams.append({
                "uid": u.uid,
                "name": u.name,
                "face": u.face,
                "fans": u.fans,
            })

        return jsonify({
            "monitor": {
                "check_interval": config.monitor.check_interval,
                "retry_times": config.monitor.retry_times,
                "retry_delay": config.monitor.retry_delay,
                "cookie": _mask_secret(config.monitor.cookie),
                "request_min": config.monitor.request_min,
                "request_max": config.monitor.request_max,
                "upstream_min": config.monitor.upstream_min,
                "upstream_max": config.monitor.upstream_max,
                "error_min": config.monitor.error_min,
                "error_max": config.monitor.error_max,
            },
            "upstreams": upstreams,
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
                "auth_token": _mask_secret(config.web.auth_token),
            },
            "notification": notification_list,
        })
    except FileNotFoundError:
        return jsonify({"error": "配置文件不存在"}), 404
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({"error": str(e)}), 500


@config_bp.route("/api/config", methods=["POST"])
def update_config() -> Any:
    """更新配置"""
    try:
        config_path = current_app.config["CONFIG_PATH"]
        raw_body = request.get_json()

        # 加载现有配置
        try:
            current_config = load_config(config_path)
        except Exception:
            current_config = AppConfig()

        # 更新监控配置（缺省字段保留磁盘现值）
        mon_old = current_config.monitor
        monitor_data = raw_body.get("monitor", {}) or {}
        existing_cookie = mon_old.cookie
        new_cookie = _keep_or_new(monitor_data.get("cookie", ""), existing_cookie)

        # 更新 UP 主列表：键缺失时保留磁盘，避免部分载荷清空
        if "upstreams" in raw_body and raw_body.get("upstreams") is not None:
            upstreams_data = raw_body.get("upstreams") or []
        else:
            upstreams_data = [
                {"uid": u.uid, "name": u.name, "face": u.face, "fans": u.fans}
                for u in current_config.upstreams
            ]

        # 更新日志配置
        logger_data = raw_body.get("logger", {}) or {}
        log_old = current_config.logger

        # 更新数据库配置
        database_data = raw_body.get("database", {}) or {}

        # 更新通知配置：键缺失时保留磁盘；掩码值保留现值
        if "notification" in raw_body and raw_body.get("notification") is not None:
            notification_list: list[NotificationConfig] = []
            for idx, n in enumerate(raw_body.get("notification") or []):
                n_type = str(n.get("type", "") or "")
                existing = _find_existing_notification(current_config.notification, n_type, idx)
                notification_list.append(_merge_notification(n, existing))
        else:
            notification_list = list(current_config.notification)

        # 构建 UP 主列表，并缓存远程头像
        from ...api.client import BiliHTTPClient
        from ...api.endpoints import BiliEndpoints
        from ...monitor.image import ImageDownloader
        avatar_downloader = ImageDownloader(
            base_dir=str(Path(config_path).parent / "images"),
            logger=logger,
        )

        # 创建 API 客户端用于自动获取信息
        api_client = None
        api_endpoints = None
        try:
            api_client = BiliHTTPClient(cookie=new_cookie, logger=logger)
            api_endpoints = BiliEndpoints(client=api_client, logger=logger)
        except Exception as e:
            logger.warning(f"创建 API 客户端失败: {e}")

        upstreams = []
        for u in upstreams_data:
            face = str(u.get("face") or "")
            uid = str(u.get("uid", ""))
            name = str(u.get("name", ""))
            fans = int(u.get("fans", 0))

            # 如果 name 或 face 为空，自动从 B站 API 获取
            if api_endpoints and (not name or not face):
                try:
                    user_info = api_endpoints.get_user_info(uid)
                    if user_info:
                        if not name and user_info.name:
                            name = user_info.name
                            logger.info(f"自动获取UP主名称: {uid} -> {name}")
                        if not face and user_info.face:
                            face = user_info.face
                            logger.info(f"自动获取UP主头像URL: {uid}")
                        if not fans:
                            fans = api_endpoints.get_user_fans(uid)
                except Exception as e:
                    logger.warning(f"自动获取UP主信息失败: {uid}, {e}")

            # 如果 face 是远程 URL，下载到本地缓存
            if face and face.startswith("http"):
                local_face = avatar_downloader.download_avatar(face, uid)
                if local_face:
                    face = local_face

            upstreams.append(UpstreamConfig(
                uid=uid,
                name=name,
                face=face,
                fans=fans,
            ))

        # 关闭 API 客户端
        if api_client:
            try:
                api_client.close()
            except Exception:
                pass

        new_config = AppConfig(
            monitor=MonitorConfig(
                check_interval=int(monitor_data.get("check_interval", mon_old.check_interval)),
                retry_times=int(monitor_data.get("retry_times", mon_old.retry_times)),
                retry_delay=int(monitor_data.get("retry_delay", mon_old.retry_delay)),
                cookie=new_cookie,
                request_min=float(monitor_data.get("request_min", mon_old.request_min)),
                request_max=float(monitor_data.get("request_max", mon_old.request_max)),
                upstream_min=float(monitor_data.get("upstream_min", mon_old.upstream_min)),
                upstream_max=float(monitor_data.get("upstream_max", mon_old.upstream_max)),
                error_min=float(monitor_data.get("error_min", mon_old.error_min)),
                error_max=float(monitor_data.get("error_max", mon_old.error_max)),
            ),
            upstreams=upstreams,
            logger=LoggerConfig(
                level=str(logger_data.get("level", log_old.level)),
                file=str(logger_data.get("file", log_old.file)),
                max_bytes=int(logger_data.get("max_bytes", log_old.max_bytes)),
                backup_count=int(logger_data.get("backup_count", log_old.backup_count)),
            ),
            database=DatabaseConfig(
                path=str(database_data.get("path", current_config.database.path)),
            ),
            web=WebConfig(
                host=current_config.web.host,
                port=current_config.web.port,
                auth_token=_keep_or_new(
                    (raw_body.get("web") or {}).get("auth_token", ""),
                    current_config.web.auth_token,
                ),
            ),
            notification=notification_list,
        )

        # 保存配置
        save_config(new_config, config_path)
        current_app.config["APP_CONFIG"] = new_config

        # 热更新监控配置
        monitor = current_app.config.get("MONITOR_INSTANCE")
        if monitor and monitor._running:
            monitor._config = new_config
            # 同步更新抖动间隔
            m = new_config.monitor
            monitor.INTERVAL_CONFIG["upstream_check"] = (m.upstream_min, m.upstream_max)
            monitor.INTERVAL_CONFIG["error_retry"] = (m.error_min, m.error_max)
            # 同步更新 HTTP 客户端的 Cookie 和限流
            if monitor._client:
                if new_config.monitor.cookie:
                    monitor._client._session.headers["Cookie"] = new_config.monitor.cookie
                monitor._client.RATE_LIMIT_CONFIG["min_interval"] = m.request_min
                monitor._client.RATE_LIMIT_CONFIG["max_interval"] = m.request_max
            # 同步更新 Cookie 服务
            if monitor._cookie_service:
                monitor._cookie_service.update_cookie(new_config.monitor.cookie)
            logger.info("监控配置已热更新")

        return jsonify({"success": True, "message": "配置已保存"})

    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
