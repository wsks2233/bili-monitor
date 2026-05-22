"""Cookie 服务

整合 Cookie 验证、检查、保活、登录等功能。
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from ..api.client import BiliHTTPClient
from ..api.endpoints import APIURL
from .checker import CookieChecker, CookieStatus
from .validator import CookieValidator


@dataclass
class LoginStatus:
    """登录状态"""
    success: bool
    status: int  # 0: 成功，86038: 二维码已过期，86090: 已扫码待确认
    message: str
    cookie: str | None = None
    username: str | None = None
    uid: int | None = None


class CookieService:
    """Cookie 统一服务
    
    使用示例：
        service = CookieService(cookie="your_cookie")
        status = service.check_status()
        service.start_keepalive()
        service.close()
    """
    
    def __init__(
        self,
        cookie: str = "",
        status_path: str = "data/cookie_status.json",
        logger: logging.Logger | None = None,
    ) -> None:
        self._cookie = cookie
        self._status_path = Path(status_path)
        self._logger = logger or logging.getLogger("bili-monitor.cookie")
        
        self._checker: CookieChecker | None = None
        self._client: BiliHTTPClient | None = None
        
        # 保活线程
        self._running = False
        self._keepalive_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        
        # 状态历史
        self._status_history: list[dict[str, Any]] = []
        self._load_status()
        
        # 回调函数
        self.on_cookie_expired: Callable[[CookieStatus], None] | None = None
        
        # 初始化
        if cookie:
            self._init_services()
    
    def _init_services(self) -> None:
        """初始化服务"""
        validation = CookieValidator.validate(self._cookie)
        if not validation["valid"]:
            self._logger.warning(f"Cookie 格式无效: {validation['message']}")
            return
        
        if not validation.get("has_login", False):
            self._logger.warning("Cookie 不含登录态，动态接口可能需要登录 Cookie")
        
        self._checker = CookieChecker(cookie=self._cookie, logger=self._logger)
        self._client = BiliHTTPClient(cookie=self._cookie, logger=self._logger)
    
    def _load_status(self) -> None:
        """加载状态历史"""
        if self._status_path.exists():
            try:
                with open(self._status_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._status_history = data.get("history", [])
            except Exception as e:
                self._logger.warning(f"加载 Cookie 状态历史失败: {e}")
    
    def _save_status(self) -> None:
        """保存状态历史"""
        self._status_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._status_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "history": self._status_history[-100:],  # 只保留最近 100 条
                        "updated_at": datetime.now().isoformat(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            self._logger.warning(f"保存 Cookie 状态失败: {e}")
    
    def check_status(self) -> CookieStatus:
        """检查 Cookie 状态"""
        if not self._checker:
            return CookieStatus(
                is_valid=False,
                uid=0,
                username="",
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message="未配置 Cookie",
            )
        
        status = self._checker.check()
        
        # 记录状态
        self._status_history.append({
            "is_valid": status.is_valid,
            "uid": status.uid,
            "username": status.username,
            "check_time": status.check_time,
            "message": status.message,
        })
        self._save_status()
        
        # 触发回调
        if not status.is_valid and self.on_cookie_expired:
            self.on_cookie_expired(status)
        
        return status
    
    def start_keepalive(self) -> None:
        """启动 Cookie 保活"""
        if not self._checker:
            self._logger.warning("Cookie 检查器未初始化，无法启动保活")
            return
        
        if self._running:
            self._logger.warning("保活线程已在运行")
            return
        
        self._running = True
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop,
            daemon=True,
            name="CookieKeepalive",
        )
        self._keepalive_thread.start()
        self._logger.info("Cookie 保活已启动")
    
    def stop_keepalive(self) -> None:
        """停止 Cookie 保活"""
        self._running = False
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=5)
        self._logger.info("Cookie 保活已停止")
    
    def _keepalive_loop(self) -> None:
        """保活循环"""
        while self._running:
            try:
                self._do_keepalive()
                # 等待 30 分钟
                for _ in range(1800):
                    if not self._running:
                        break
                    time.sleep(1)
            except Exception as e:
                self._logger.error(f"保活循环异常: {e}")
                time.sleep(60)
    
    def _do_keepalive(self) -> None:
        """执行保活操作"""
        self._logger.info("执行 Cookie 保活...")
        
        try:
            # 访问首页
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Cookie": self._cookie,
            })
            
            response = session.get("https://www.bilibili.com/", timeout=30)
            if response.status_code == 200:
                self._logger.info("Cookie 保活成功")
            else:
                self._logger.warning(f"Cookie 保活失败: HTTP {response.status_code}")
            
            session.close()
        except Exception as e:
            self._logger.error(f"保活失败: {e}")
    
    def get_remaining_days(self) -> int | None:
        """估算 Cookie 剩余有效天数"""
        if len(self._status_history) < 2:
            return None
        
        first_check = self._status_history[0].get("check_time", "")
        if not first_check:
            return None
        
        try:
            first_time = datetime.fromisoformat(first_check)
            elapsed_days = (datetime.now() - first_time).days
            return max(0, 30 - elapsed_days)
        except Exception:
            return None
    
    def update_cookie(self, new_cookie: str) -> bool:
        """更新 Cookie"""
        with self._lock:
            self._logger.info("开始更新 Cookie...")
            
            # 停止保活
            was_running = self._running
            self.stop_keepalive()
            
            # 更新 Cookie
            self._cookie = new_cookie
            
            # 关闭旧服务
            if self._checker:
                self._checker.close()
            if self._client:
                self._client.close()
            
            # 初始化新服务
            self._init_services()
            
            # 重新启动保活
            if was_running and self._checker:
                self.start_keepalive()
            
            self._logger.info("Cookie 更新完成")
            return True
    
    def get_qrcode(self) -> tuple[str, str]:
        """获取登录二维码"""
        if not self._client:
            self._client = BiliHTTPClient(logger=self._logger)
        
        try:
            data = self._client.get(APIURL.QRCODE_GENERATE)
            
            if data.get("code") == 0:
                qrcode_url = data["data"].get("url", "")
                qrcode_key = data["data"].get("qrcode_key", "")
                if qrcode_url and qrcode_key:
                    return qrcode_url, qrcode_key
            
            raise Exception("获取二维码失败")
        except Exception as e:
            self._logger.error(f"获取二维码失败: {e}")
            raise
    
    def check_login(self, qrcode_key: str) -> LoginStatus:
        """检查登录状态"""
        if not self._client:
            self._client = BiliHTTPClient(logger=self._logger)
        
        try:
            data = self._client.get(APIURL.QRCODE_POLL, {"qrcode_key": qrcode_key})
            
            if data.get("code") != 0:
                return LoginStatus(
                    success=False,
                    status=-1,
                    message=data.get("message", "请求失败"),
                )
            
            login_data = data.get("data", {})
            status_code = login_data.get("code", -1)
            
            if status_code == 0:
                # 登录成功，提取 Cookie
                cookie = self._extract_cookie()
                user_info = self._get_user_info(cookie)
                
                return LoginStatus(
                    success=True,
                    status=0,
                    message="登录成功",
                    cookie=cookie,
                    username=user_info.get("username"),
                    uid=user_info.get("uid"),
                )
            else:
                messages = {
                    86101: "未扫码",
                    86090: "已扫码待确认",
                    86038: "二维码已过期",
                }
                return LoginStatus(
                    success=False,
                    status=status_code,
                    message=messages.get(status_code, f"未知状态: {status_code}"),
                )
        except Exception as e:
            self._logger.error(f"检查登录状态失败: {e}")
            return LoginStatus(
                success=False,
                status=-1,
                message=str(e),
            )
    
    def _extract_cookie(self) -> str:
        """从 session 中提取 Cookie"""
        if not self._client:
            return ""
        
        cookies = []
        for cookie in self._client.session.cookies:
            cookies.append(f"{cookie.name}={cookie.value}")
        return "; ".join(cookies)
    
    def _get_user_info(self, cookie: str) -> dict[str, Any]:
        """获取用户信息"""
        try:
            client = BiliHTTPClient(cookie=cookie, logger=self._logger)
            try:
                data = client.get(APIURL.NAV)
                if data.get("code") == 0:
                    user_data = data.get("data", {})
                    return {
                        "username": user_data.get("uname", ""),
                        "uid": user_data.get("mid", 0),
                    }
            finally:
                client.close()
        except Exception as e:
            self._logger.error(f"获取用户信息失败: {e}")
        return {}
    
    def close(self) -> None:
        """关闭服务"""
        self.stop_keepalive()
        if self._client:
            self._client.close()
        if self._checker:
            self._checker.close()
    
    def __enter__(self) -> CookieService:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
