"""可选管理 API Token 鉴权"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable

from flask import Request, current_app, jsonify, request

logger = logging.getLogger("bili-monitor.web")

ENV_TOKEN_KEY = "BILI_MONITOR_TOKEN"

# 需要鉴权的写操作与日志读取
PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
PROTECTED_PATH_PREFIXES = ("/api/logs",)


def resolve_auth_token() -> str:
    """环境变量优先于配置文件"""
    env_token = os.environ.get(ENV_TOKEN_KEY, "").strip()
    if env_token:
        return env_token
    config = current_app.config.get("APP_CONFIG")
    if config is not None:
        return str(getattr(config.web, "auth_token", "") or "").strip()
    return ""


def _extract_token(req: Request) -> str:
    auth = req.headers.get("Authorization", "") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    header_token = req.headers.get("X-Auth-Token", "") or ""
    return header_token.strip()


def is_protected_request(req: Request) -> bool:
    path = req.path or ""
    if req.method.upper() in PROTECTED_METHODS and path.startswith("/api/"):
        return True
    return any(path.startswith(p) for p in PROTECTED_PATH_PREFIXES)


def require_token(fn: Callable[..., Any]) -> Callable[..., Any]:
    """包装路由：配置了 token 时校验写操作/日志接口"""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        expected = resolve_auth_token()
        if not expected:
            return fn(*args, **kwargs)
        if not is_protected_request(request):
            return fn(*args, **kwargs)
        provided = _extract_token(request)
        if provided != expected:
            return jsonify({"error": "未授权：缺少或错误的 API Token"}), 401
        return fn(*args, **kwargs)

    return wrapper


def register_auth(app: Any) -> None:
    """注册全局 before_request：请求时读取 token（避免工厂阶段依赖 app context）"""

    @app.before_request
    def _check_token() -> Any:
        expected = resolve_auth_token()
        if not expected:
            return None
        if not is_protected_request(request):
            return None
        provided = _extract_token(request)
        if provided != expected:
            return jsonify({"error": "未授权：缺少或错误的 API Token"}), 401
        return None
