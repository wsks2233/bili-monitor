"""Cookie 状态检查器"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..api.client import BiliHTTPClient
from ..api.endpoints import APIURL
from .validator import CookieValidator


@dataclass
class CookieStatus:
    """Cookie 状态"""
    is_valid: bool
    uid: int
    username: str
    vip_status: int
    is_login: bool
    check_time: str
    message: str


class CookieChecker:
    """Cookie 有效性检查器
    
    使用示例：
        checker = CookieChecker(cookie="your_cookie")
        status = checker.check()
        print(f"有效: {status.is_valid}, 用户: {status.username}")
        checker.close()
    """
    
    def __init__(
        self,
        cookie: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self._cookie = cookie
        self._logger = logger or logging.getLogger("bili-monitor.cookie")
        self._client: BiliHTTPClient | None = None
        
        if cookie:
            self._client = BiliHTTPClient(cookie=cookie, logger=logger)
    
    def check(self) -> CookieStatus:
        """检查 Cookie 状态"""
        if not self._cookie:
            return CookieStatus(
                is_valid=False,
                uid=0,
                username="",
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message="未配置 Cookie",
            )
        
        # 验证格式
        validation = CookieValidator.validate(self._cookie)
        if not validation["valid"]:
            return CookieStatus(
                is_valid=False,
                uid=0,
                username="",
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message=validation["message"],
            )
        
        # 检查有效性
        if not self._client:
            return CookieStatus(
                is_valid=False,
                uid=0,
                username="",
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message="客户端未初始化",
            )
        
        try:
            data = self._client.get(APIURL.NAV)
            
            if data.get("code") == 0:
                user_data = data.get("data", {})
                return CookieStatus(
                    is_valid=True,
                    uid=user_data.get("mid", 0),
                    username=user_data.get("uname", ""),
                    vip_status=user_data.get("vipStatus", 0),
                    is_login=user_data.get("isLogin", False),
                    check_time=datetime.now().isoformat(),
                    message="Cookie 有效",
                )
            else:
                return CookieStatus(
                    is_valid=False,
                    uid=0,
                    username="",
                    vip_status=0,
                    is_login=False,
                    check_time=datetime.now().isoformat(),
                    message=data.get("message", "未知错误"),
                )
        except Exception as e:
            self._logger.error(f"检查 Cookie 状态失败: {e}")
            return CookieStatus(
                is_valid=False,
                uid=0,
                username="",
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message=str(e),
            )
    
    def close(self) -> None:
        """关闭检查器"""
        if self._client:
            self._client.close()
    
    def __enter__(self) -> CookieChecker:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
