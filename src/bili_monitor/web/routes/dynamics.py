"""动态相关路由"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from flask import Blueprint, jsonify, request

logger = logging.getLogger("bili-monitor.web")

dynamics_bp = Blueprint("dynamics", __name__)


@dynamics_bp.route("/api/upstreams")
def get_upstreams() -> Any:
    """获取 UP 主列表"""
    from flask import current_app
    from ...monitor.runner import Monitor
    
    monitor: Monitor | None = current_app.config.get("MONITOR_INSTANCE")
    
    if not monitor or not monitor._db:
        return jsonify([])
    
    try:
        conn = monitor._db._conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM upstreams")
        rows = cursor.fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        logger.error(f"获取 UP 主列表失败: {e}")
        return jsonify([])


@dynamics_bp.route("/api/dynamics")
def get_dynamics() -> Any:
    """获取动态列表"""
    from flask import current_app
    from ...monitor.runner import Monitor
    
    monitor: Monitor | None = current_app.config.get("MONITOR_INSTANCE")
    
    if not monitor or not monitor._db:
        return jsonify([])
    
    try:
        uid = request.args.get("uid")
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
        
        dynamics = monitor.get_dynamics(uid, limit, offset)
        return jsonify(dynamics)
    except Exception as e:
        logger.error(f"获取动态列表失败: {e}")
        return jsonify({"error": str(e)}), 500


@dynamics_bp.route("/api/upstream/info/<uid>")
def get_upstream_info(uid: str) -> Any:
    """获取 UP 主信息"""
    from flask import current_app
    from ...api.client import BiliHTTPClient
    from ...api.endpoints import BiliEndpoints
    from ...api.client import CookieExpiredError, WBIError, UserNotFoundError, BiliAPIError
    
    try:
        config = current_app.config["APP_CONFIG"]
        
        client = BiliHTTPClient(cookie=config.monitor.cookie, logger=logger)
        api = BiliEndpoints(client=client, logger=logger)
        
        try:
            user_info = api.get_user_info(uid)
            fans = api.get_user_fans(uid)
            
            if user_info and user_info.name:
                return jsonify({
                    "uid": uid,
                    "name": user_info.name,
                    "face": user_info.face,
                    "sign": user_info.sign,
                    "level": user_info.level,
                    "fans": fans,
                })
            else:
                return jsonify({"error": f"未找到用户 {uid}"}), 404
        finally:
            client.close()
    
    except CookieExpiredError as e:
        return jsonify({"error": str(e)}), 401
    except WBIError as e:
        return jsonify({"error": str(e)}), 403
    except UserNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except BiliAPIError as e:
        return jsonify({"error": f"B站 API 错误: {e}"}), 502
    except Exception as e:
        logger.error(f"获取 UP 主信息失败: {e}")
        return jsonify({"error": str(e)}), 500
