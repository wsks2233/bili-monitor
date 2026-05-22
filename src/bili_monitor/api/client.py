"""HTTP 客户端

统一的 HTTP 客户端，包含：
- 请求限流
- 自动重试
- WBI 签名
- Cookie 管理
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .wbi import WBISigner


class BiliAPIError(Exception):
    """B站 API 错误"""
    
    def __init__(self, message: str, code: int = 0) -> None:
        super().__init__(message)
        self.code = code


class RateLimitError(BiliAPIError):
    """频率限制错误"""
    pass


class CookieExpiredError(BiliAPIError):
    """Cookie 失效错误"""
    pass


class WBIError(BiliAPIError):
    """WBI 签名错误"""
    pass


class UserNotFoundError(BiliAPIError):
    """用户不存在错误"""
    pass


class BiliHTTPClient:
    """B站 HTTP 客户端
    
    使用示例：
        client = BiliHTTPClient(cookie="your_cookie")
        data = client.get("https://api.bilibili.com/x/web-interface/nav")
        client.close()
    """
    
    # 默认请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://t.bilibili.com",
        "Referer": "https://t.bilibili.com/",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }
    
    # 限流配置
    RATE_LIMIT_CONFIG = {
        "min_interval": 1.5,
        "max_interval": 3.0,
        "retry_base": 5.0,
        "retry_jitter": 3.0,
    }
    
    def __init__(
        self,
        cookie: str = "",
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger("bili-monitor.api")
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)
        
        # 设置设备 Cookie
        self._init_device_cookies()
        
        # 设置用户 Cookie
        if cookie:
            self._session.headers["Cookie"] = cookie
        
        # WBI 签名器
        self._wbi = WBISigner()
        
        # 限流状态
        self._last_request_time: float = 0
    
    def _init_device_cookies(self) -> None:
        """初始化设备 Cookie"""
        import uuid
        
        buvid3 = f"{uuid.uuid4().hex.upper()[:8]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:12]}infoc"
        buvid4 = f"{uuid.uuid4().hex.upper()[:8]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:12]}-{int(time.time())}-0"
        _uuid = f"{uuid.uuid4().hex.upper()[:8]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:4]}-{uuid.uuid4().hex.upper()[:12]}infoc"
        
        self._session.cookies.set("buvid3", buvid3, domain=".bilibili.com")
        self._session.cookies.set("buvid4", buvid4, domain=".bilibili.com")
        self._session.cookies.set("_uuid", _uuid, domain=".bilibili.com")
        self._session.cookies.set("CURRENT_FNVAL", "4048", domain=".bilibili.com")
        self._session.cookies.set("CURRENT_QUALITY", "80", domain=".bilibili.com")
        self._session.cookies.set("enable_web_push", "DISABLE", domain=".bilibili.com")
        self._session.cookies.set("home_feed_column", "5", domain=".bilibili.com")
        self._session.cookies.set("browser_resolution", "1920-1000", domain=".bilibili.com")
    
    def _wait_for_rate_limit(self) -> None:
        """等待以避免频率限制"""
        elapsed = time.time() - self._last_request_time
        min_interval = random.uniform(
            self.RATE_LIMIT_CONFIG["min_interval"],
            self.RATE_LIMIT_CONFIG["max_interval"],
        )
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed + random.uniform(0.2, 0.8)
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def update_cookie(self, cookie: str) -> None:
        """更新 Cookie
        
        Args:
            cookie: 新的 Cookie 字符串
        """
        self._session.headers["Cookie"] = cookie
    
    @property
    def wbi(self) -> WBISigner:
        """获取 WBI 签名器"""
        return self._wbi
    
    @property
    def session(self) -> requests.Session:
        """获取底层 Session（用于特殊场景）"""
        return self._session
    
    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """发送 GET 请求
        
        Args:
            url: 请求 URL
            params: 查询参数
            max_retries: 最大重试次数
            
        Returns:
            API 响应数据
            
        Raises:
            BiliAPIError: API 错误
            RateLimitError: 频率限制
            CookieExpiredError: Cookie 失效
            WBIError: WBI 签名失败
            UserNotFoundError: 用户不存在
        """
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                code = data.get("code", 0)
                
                # 频率限制
                if code == -799:
                    wait_time = (
                        (attempt + 1) * self.RATE_LIMIT_CONFIG["retry_base"]
                        + random.uniform(1, self.RATE_LIMIT_CONFIG["retry_jitter"])
                    )
                    self._logger.warning(
                        f"触发频率限制，等待 {wait_time:.1f} 秒后重试 "
                        f"({attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                
                # 其他错误
                if code != 0:
                    error_msg = data.get("message", "Unknown error")
                    self._logger.error(f"API 错误 [{code}]: {error_msg}, URL: {url}")
                    
                    if code == -352:
                        # WBI 签名失败，清除缓存
                        self._wbi = WBISigner()
                        raise WBIError("WBI 签名校验失败", code)
                    elif code == -101:
                        raise CookieExpiredError("Cookie 已失效或未登录", code)
                    elif code == -400:
                        raise BiliAPIError(f"请求参数错误: {error_msg}", code)
                    elif code == -404:
                        raise UserNotFoundError("用户不存在或已被封禁", code)
                    elif code == -412:
                        raise BiliAPIError("请求被拦截，请检查网络环境", code)
                    else:
                        raise BiliAPIError(f"API 返回错误 [{code}]: {error_msg}", code)
                
                return data
                
            except requests.RequestException as e:
                self._logger.error(f"请求失败: {e}, URL: {url}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 4))
                    continue
                raise
        
        raise BiliAPIError("请求失败，超过最大重试次数")
    
    def get_signed(
        self,
        url: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """发送带 WBI 签名的 GET 请求
        
        Args:
            url: 请求 URL
            params: 原始参数（会被签名）
            max_retries: 最大重试次数
            
        Returns:
            API 响应数据
        """
        signed_params = self._wbi.sign(params.copy())
        return self.get(url, signed_params, max_retries)
    
    def close(self) -> None:
        """关闭客户端"""
        self._session.close()
    
    def __enter__(self) -> BiliHTTPClient:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
