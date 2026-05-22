"""Flask 应用工厂"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import json
import queue
import threading

from flask import Flask
from flask_cors import CORS

from ..config.loader import load_config
from ..config.models import AppConfig


class EventBus:
    def __init__(self):
        self._subscribers: list[queue.Queue] = []
        self._lock = threading.Lock()
    
    def subscribe(self) -> queue.Queue:
        q = queue.Queue()
        with self._lock:
            self._subscribers.append(q)
        return q
    
    def unsubscribe(self, q: queue.Queue):
        with self._lock:
            self._subscribers.remove(q)
    
    def publish(self, event: dict):
        with self._lock:
            for q in self._subscribers:
                q.put(event)


def create_app(config_path: str = "config.yaml") -> Flask:
    """创建 Flask 应用
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)
    app.config["EVENT_BUS"] = EventBus()
    
    # 加载配置
    try:
        config = load_config(config_path)
    except Exception:
        config = AppConfig()
    
    # 存储配置到 app
    app.config["APP_CONFIG"] = config
    app.config["CONFIG_PATH"] = config_path
    
    # 配置 CORS
    CORS(app)
    
    # 注册蓝图
    from .routes.config import config_bp
    from .routes.dynamics import dynamics_bp
    from .routes.login import login_bp
    from .routes.monitor import monitor_bp
    
    app.register_blueprint(config_bp)
    app.register_blueprint(dynamics_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(monitor_bp)
    
    # 静态文件
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        @app.route("/")
        def index() -> Any:
            from flask import send_from_directory
            return send_from_directory(str(static_dir), "index.html")
        
        @app.route("/favicon.ico")
        def favicon() -> Any:
            from flask import send_from_directory
            return send_from_directory(str(static_dir), "favicon.ico")
    else:
        @app.route("/")
        def index() -> dict[str, str]:
            return {"message": "B站动态监控 API 服务运行中"}
    
    # 图片静态文件
    images_dir = Path("images")
    if images_dir.exists():
        @app.route("/images/<path:filename>")
        def serve_image(filename: str) -> Any:
            from flask import send_from_directory
            return send_from_directory(str(images_dir), filename)
    
    # 健康检查
    @app.route("/api/status")
    def health_check() -> dict[str, Any]:
        from ..monitor.runner import Monitor
        monitor: Monitor | None = app.config.get("MONITOR_INSTANCE")
        
        running = monitor is not None and monitor._running
        stats = monitor.get_stats() if monitor else {}
        cookie_status = monitor.get_cookie_status() if monitor else {"valid": False}
        
        return {
            "running": running,
            "total_dynamics": stats.get("total_dynamics", 0),
            "total_upstreams": stats.get("total_upstreams", 0),
            "cookie_valid": cookie_status.get("valid", False),
            "cookie_username": cookie_status.get("username"),
        }
    
    # SSE 端点
    @app.route("/api/events")
    def sse_events() -> Any:
        from flask import Response, stream_with_context
        
        def generate():
            from ..monitor.runner import Monitor
            event_bus: EventBus = app.config["EVENT_BUS"]
            q = event_bus.subscribe()
            try:
                # 立即推送当前状态快照
                monitor: Monitor | None = app.config.get("MONITOR_INSTANCE")
                running = monitor is not None and monitor._running
                stats = monitor.get_stats() if monitor else {}
                cookie_status = monitor.get_cookie_status() if monitor else {"valid": False}
                initial_data = {
                    "running": running,
                    "total_dynamics": stats.get("total_dynamics", 0),
                    "total_upstreams": stats.get("total_upstreams", 0),
                    "cookie_valid": cookie_status.get("valid", False),
                    "cookie_username": cookie_status.get("username"),
                }
                yield f"data: {json.dumps(initial_data)}\n\n"
                
                while True:
                    try:
                        data = q.get(timeout=30)
                        yield f"data: {json.dumps(data)}\n\n"
                    except queue.Empty:
                        # 心跳
                        yield ": heartbeat\n\n"
            except GeneratorExit:
                # 客户端断开
                event_bus.unsubscribe(q)
            finally:
                # 确保清理
                try:
                    event_bus.unsubscribe(q)
                except ValueError:
                    pass
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    return app
