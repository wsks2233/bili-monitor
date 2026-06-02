"""登录相关路由"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from ...config.loader import load_config, save_config
from ...config.models import AppConfig, MonitorConfig
from ...cookie.service import CookieService
from ...cookie.validator import CookieValidator

logger = logging.getLogger("bili-monitor.web")

login_bp = Blueprint("login", __name__)


def _get_cookie_service() -> CookieService:
    """获取 Cookie 服务"""
    service: CookieService | None = current_app.config.get("COOKIE_SERVICE")
    
    if not service:
        config_path = current_app.config["CONFIG_PATH"]
        config = load_config(config_path)
        
        service = CookieService(
            cookie=config.monitor.cookie,
            logger=logger,
        )
        current_app.config["COOKIE_SERVICE"] = service
    
    return service


@login_bp.route("/api/login/qrcode")
def get_login_qrcode() -> Any:
    """获取登录二维码"""
    try:
        service = _get_cookie_service()
        qrcode_url, qrcode_key = service.get_qrcode()
        
        if not qrcode_url or not qrcode_key:
            return jsonify({"error": "获取二维码失败"}), 500
        
        # 生成二维码图片
        qrcode_image = None
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qrcode_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            qrcode_image = f"data:image/png;base64,{img_base64}"
        except ImportError:
            pass
        
        return jsonify({
            "success": True,
            "qrcode_key": qrcode_key,
            "qrcode_url": qrcode_url,
            "qrcode_image": qrcode_image,
        })
    
    except Exception as e:
        logger.error(f"获取二维码失败: {e}")
        return jsonify({"error": str(e)}), 500


@login_bp.route("/api/login/check")
def check_login_status() -> Any:
    """检查登录状态"""
    try:
        qrcode_key = request.args.get("qrcode_key")
        if not qrcode_key:
            return jsonify({"error": "缺少 qrcode_key 参数"}), 400
        
        service = _get_cookie_service()
        status = service.check_login(qrcode_key)
        
        if status.success:
            # 保存 Cookie 到配置文件
            config_path = current_app.config["CONFIG_PATH"]
            config = load_config(config_path)
            
            from ...config.models import AppConfig
            new_config = AppConfig(
                monitor=MonitorConfig(
                    check_interval=config.monitor.check_interval,
                    retry_times=config.monitor.retry_times,
                    retry_delay=config.monitor.retry_delay,
                    cookie=status.cookie,
                ),
                upstreams=config.upstreams,
                logger=config.logger,
                database=config.database,
                web=config.web,
                notification=config.notification,
            )
            save_config(new_config, config_path)
            current_app.config["APP_CONFIG"] = new_config

            # 更新监控实例
            monitor = current_app.config.get("MONITOR_INSTANCE")
            if monitor:
                monitor._config = new_config
                # 同步更新 HTTP 客户端的 Cookie
                if monitor._client:
                    monitor._client._session.headers["Cookie"] = status.cookie

            # 更新 Cookie 服务
            service.update_cookie(status.cookie)
            
            return jsonify({
                "success": True,
                "status": 0,
                "message": "登录成功，Cookie 已保存",
                "username": status.username,
            })
        else:
            return jsonify({
                "success": False,
                "status": status.status,
                "message": status.message,
            })
    
    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
        return jsonify({"error": str(e)}), 500


@login_bp.route("/api/login/cookie", methods=["POST"])
def set_cookie_directly() -> Any:
    """直接设置 Cookie"""
    try:
        data = request.get_json()
        cookie = data.get("cookie", "")
        
        if not cookie:
            return jsonify({"success": False, "message": "Cookie 不能为空"})
        
        # 验证 Cookie
        validation = CookieValidator.validate(cookie)
        if not validation["valid"]:
            return jsonify({
                "success": False,
                "message": f"Cookie 格式无效: {validation['message']}",
            })
        
        if not validation.get("has_login", False):
            return jsonify({
                "success": False,
                "message": "Cookie 缺少登录字段，请确保包含 SESSDATA、bili_jct、DedeUserID",
            })
        
        # 保存到配置文件
        config_path = current_app.config["CONFIG_PATH"]
        config = load_config(config_path)
        
        from ...config.models import AppConfig
        new_config = AppConfig(
            monitor=MonitorConfig(
                check_interval=config.monitor.check_interval,
                retry_times=config.monitor.retry_times,
                retry_delay=config.monitor.retry_delay,
                cookie=cookie,
            ),
            upstreams=config.upstreams,
            logger=config.logger,
            database=config.database,
            web=config.web,
            notification=config.notification,
        )
        save_config(new_config, config_path)
        current_app.config["APP_CONFIG"] = new_config
        
        # 更新监控实例
        monitor = current_app.config.get("MONITOR_INSTANCE")
        if monitor:
            monitor._config = new_config
            # 同步更新 HTTP 客户端的 Cookie
            if monitor._client:
                monitor._client._session.headers["Cookie"] = cookie
        
        # 更新 Cookie 服务
        service = current_app.config.get("COOKIE_SERVICE")
        if service:
            service.update_cookie(cookie)
        
        return jsonify({"success": True, "message": "Cookie 已保存，请重启监控服务"})
    
    except Exception as e:
        logger.error(f"设置 Cookie 失败: {e}")
        return jsonify({"error": str(e)}), 500
