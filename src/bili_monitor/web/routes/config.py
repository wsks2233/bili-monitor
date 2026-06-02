"""配置相关路由"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from ...config.loader import load_config, save_config
from ...config.models import AppConfig, DatabaseConfig, LoggerConfig, MonitorConfig, NotificationConfig, UpstreamConfig

logger = logging.getLogger("bili-monitor.web")

config_bp = Blueprint("config", __name__)


def _mask_cookie(cookie: str) -> str:
    """掩码 Cookie"""
    if not cookie or len(cookie) < 20:
        return cookie[:5] + "..." if cookie else ""
    return cookie[:10] + "..." + cookie[-5:]


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
                "webhook_url": _mask_cookie(n.webhook_url) if n.webhook_url else "",
                "secret": n.secret,
                "serverchan_key": _mask_cookie(n.serverchan_key) if n.serverchan_key else "",
                "pushplus_token": _mask_cookie(n.pushplus_token) if n.pushplus_token else "",
                "smtp_server": n.smtp_server,
                "smtp_port": n.smtp_port,
                "smtp_user": n.smtp_user,
                "smtp_password": "******" if n.smtp_password else "",
                "sender": n.sender,
                "receivers": n.receivers,
                "bot_token": _mask_cookie(n.bot_token) if n.bot_token else "",
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
                "cookie": _mask_cookie(config.monitor.cookie),
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
        
        # 更新监控配置
        monitor_data = raw_body.get("monitor", {})
        existing_cookie = current_config.monitor.cookie
        
        # 处理 Cookie
        new_cookie = existing_cookie
        if monitor_data.get("cookie"):
            if not str(monitor_data["cookie"]).endswith("..."):
                new_cookie = monitor_data["cookie"]
        
        # 更新 UP 主列表
        upstreams_data = raw_body.get("upstreams", [])
        
        # 更新日志配置
        logger_data = raw_body.get("logger", {})
        
        # 更新数据库配置
        database_data = raw_body.get("database", {})
        
        # 更新通知配置
        notification_data = raw_body.get("notification", [])
        notification_list = []
        for n in notification_data:
            n_dict = {"type": n.get("type", "")}
            
            webhook_url = str(n.get("webhook_url", ""))
            if webhook_url and not webhook_url.endswith("..."):
                n_dict["webhook_url"] = webhook_url
            
            secret = str(n.get("secret", ""))
            if secret:
                n_dict["secret"] = secret
            
            serverchan_key = str(n.get("serverchan_key", ""))
            if serverchan_key and not serverchan_key.endswith("..."):
                n_dict["serverchan_key"] = serverchan_key
            
            pushplus_token = str(n.get("pushplus_token", ""))
            if pushplus_token and not pushplus_token.endswith("..."):
                n_dict["pushplus_token"] = pushplus_token
            
            smtp_server = str(n.get("smtp_server", ""))
            if smtp_server:
                n_dict["smtp_server"] = smtp_server
                n_dict["smtp_port"] = int(n.get("smtp_port", 465))
                n_dict["smtp_user"] = str(n.get("smtp_user", ""))
                smtp_password = str(n.get("smtp_password", ""))
                if smtp_password == "******":
                    # 保持现有密码不变
                    existing_notif = next(
                        (x for x in current_config.notification if x.type == "email"), None
                    )
                    if existing_notif:
                        n_dict["smtp_password"] = existing_notif.smtp_password
                elif smtp_password:
                    n_dict["smtp_password"] = smtp_password
                n_dict["sender"] = str(n.get("sender", ""))
                receivers = n.get("receivers", [])
                if isinstance(receivers, list):
                    n_dict["receivers"] = [str(r) for r in receivers]
                else:
                    n_dict["receivers"] = []
            
            bot_token = str(n.get("bot_token", ""))
            if bot_token and not bot_token.endswith("..."):
                n_dict["bot_token"] = bot_token
                n_dict["chat_id"] = str(n.get("chat_id", ""))
            
            notification_list.append(n_dict)
        
        # 构建 UP 主列表，并缓存远程头像
        from ...monitor.image import ImageDownloader
        avatar_downloader = ImageDownloader(base_dir="images", logger=logger)

        upstreams = []
        for u in upstreams_data:
            face = str(u.get("face") or "")
            uid = str(u.get("uid", ""))
            # 如果 face 是远程 URL，下载到本地缓存
            if face and face.startswith("http"):
                local_face = avatar_downloader.download_avatar(face, uid)
                if local_face:
                    face = local_face
            upstreams.append(UpstreamConfig(
                uid=uid,
                name=str(u.get("name", "")),
                face=face,
                fans=int(u.get("fans", 0)),
            ))

        new_config = AppConfig(
            monitor=MonitorConfig(
                check_interval=int(monitor_data.get("check_interval", 300)),
                retry_times=int(monitor_data.get("retry_times", 3)),
                retry_delay=int(monitor_data.get("retry_delay", 5)),
                cookie=new_cookie,
                request_min=float(monitor_data.get("request_min", 1.5)),
                request_max=float(monitor_data.get("request_max", 3.0)),
                upstream_min=float(monitor_data.get("upstream_min", 2.0)),
                upstream_max=float(monitor_data.get("upstream_max", 5.0)),
                error_min=float(monitor_data.get("error_min", 3.0)),
                error_max=float(monitor_data.get("error_max", 6.0)),
            ),
            upstreams=upstreams,
            logger=LoggerConfig(
                level=str(logger_data.get("level", "INFO")),
                file=str(logger_data.get("file", "logs/bili-monitor.log")),
                max_bytes=int(logger_data.get("max_bytes", 10 * 1024 * 1024)),
                backup_count=int(logger_data.get("backup_count", 5)),
            ),
            database=DatabaseConfig(
                path=str(database_data.get("path", "data/bili_monitor.db")),
            ),
            web=current_config.web,
            notification=[
                NotificationConfig(**n) for n in notification_list
            ],
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
