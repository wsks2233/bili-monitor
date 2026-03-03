# -*- coding: utf-8 -*-
"""
B 站 Cookie 统一服务接口

提供以下功能：
1. Cookie 有效性检测
2. Cookie 保活管理
3. Cookie 状态查询
4. Cookie 更新与持久化
5. 扫码登录支持

使用示例：
```python
from bili_monitor.api.cookie_service import CookieService

# 创建服务实例
cookie_service = CookieService(config_path="config.yaml")

# 检查 Cookie 状态
status = cookie_service.check_status()
print(f"Cookie 有效：{status.is_valid}, 用户：{status.username}")

# 启动保活
cookie_service.start_keepalive()

# 扫码登录
qrcode_url, qrcode_key = cookie_service.get_qrcode()
# ... 用户扫码 ...
login_status = cookie_service.check_login(qrcode_key)
if login_status.success:
    print(f"登录成功，Cookie: {login_status.cookie}")
```
"""

import logging
import os
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
import requests

from .cookie_manager import CookieManager, CookieValidator, CookieStatus
from .bili_api import BiliAPI


@dataclass
class LoginStatus:
    """登录状态"""
    success: bool
    status: int  # 0: 成功，86038: 二维码已过期，86090: 已扫码待确认
    message: str
    cookie: Optional[str] = None
    username: Optional[str] = None
    uid: Optional[int] = None


@dataclass
class ServiceStatus:
    """服务状态"""
    is_valid: bool
    uid: int
    username: str
    vip_status: int
    is_login: bool
    check_time: str
    message: str
    remaining_days: Optional[int] = None
    
    @classmethod
    def from_cookie_status(cls, status: CookieStatus, remaining_days: Optional[int] = None):
        return cls(
            is_valid=status.is_valid,
            uid=status.uid,
            username=status.username,
            vip_status=status.vip_status,
            is_login=status.is_login,
            check_time=status.check_time,
            message=status.message,
            remaining_days=remaining_days
        )


class CookieService:
    """
    Cookie 统一服务类
    
    整合了 Cookie 管理、验证、保活、登录等功能
    """
    
    def __init__(
        self,
        cookie: str = "",
        config_path: str = "config.yaml",
        logger: Optional[logging.Logger] = None,
    ):
        """
        初始化 Cookie 服务
        
        Args:
            cookie: Cookie 字符串
            config_path: 配置文件路径
            logger: 日志记录器
        """
        self.cookie = cookie
        self.config_path = config_path
        self.logger = logger or logging.getLogger('bili-monitor.cookie')
        
        self._cookie_manager: Optional[CookieManager] = None
        self._api: Optional[BiliAPI] = None
        self._running = False
        self._lock = threading.Lock()
        
        # 回调函数
        self.on_cookie_expired: Optional[Callable[[ServiceStatus], None]] = None
        
        # 初始化
        if cookie:
            self._init_manager()
    
    def _init_manager(self):
        """初始化 Cookie 管理器"""
        if not self.cookie:
            return
        
        validation = CookieValidator.validate(self.cookie)
        if not validation['valid']:
            self.logger.warning(f"Cookie 格式无效：{validation['message']}")
            return
        
        if not validation.get('has_login', False):
            self.logger.warning(f"Cookie 不含登录态：{validation['message']}")
            self.logger.warning("动态接口可能需要登录Cookie才能正常工作")
        
        self._cookie_manager = CookieManager(
            cookie=self.cookie,
            logger=self.logger,
            config_path="data/cookie_status.json",
            check_interval=3600,
            keepalive_interval=1800,
        )
        
        def on_expired(status):
            service_status = ServiceStatus.from_cookie_status(status)
            if self.on_cookie_expired:
                self.on_cookie_expired(service_status)
        
        self._cookie_manager.on_expired = on_expired
        
        self._api = BiliAPI(self.logger, cookie=self.cookie)
    
    def check_status(self) -> ServiceStatus:
        """
        检查 Cookie 状态
        
        Returns:
            ServiceStatus: Cookie 状态信息
        """
        if not self._cookie_manager:
            return ServiceStatus(
                is_valid=False,
                uid=0,
                username='',
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message="未配置 Cookie"
            )
        
        status = self._cookie_manager.check_cookie_status()
        remaining_days = self._cookie_manager.get_remaining_days()
        
        return ServiceStatus.from_cookie_status(status, remaining_days)
    
    def start_keepalive(self):
        """启动 Cookie 保活"""
        if not self._cookie_manager:
            self.logger.warning("Cookie 管理器未初始化，无法启动保活")
            return
        
        with self._lock:
            if self._running:
                self.logger.warning("保活线程已在运行")
                return
            
            self._running = True
            self._cookie_manager.start_keepalive()
            self.logger.info("Cookie 保活已启动")
    
    def stop_keepalive(self):
        """停止 Cookie 保活"""
        if not self._cookie_manager:
            return
        
        with self._lock:
            self._running = False
            self._cookie_manager.stop_keepalive()
    
    def update_cookie(self, new_cookie: str, save_to_config: bool = True, timeout: float = 5.0):
        """
        更新 Cookie
        
        Args:
            new_cookie: 新的 Cookie
            save_to_config: 是否保存到配置文件
            timeout: 获取锁的超时时间（秒）
        """
        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            self.logger.warning(f"获取 Cookie 更新锁超时，跳过更新")
            return False
        
        try:
            # 停止旧的保活
            self.stop_keepalive()
            
            # 更新 Cookie
            self.cookie = new_cookie
            
            # 重新初始化管理器
            if self._cookie_manager:
                self._cookie_manager.close()
            if self._api:
                self._api.close()
            
            self._init_manager()
            
            # 启动新的保活
            if self._cookie_manager:
                self.start_keepalive()
            
            # 保存到配置文件
            if save_to_config and new_cookie:
                self._save_cookie_to_config(new_cookie)
            
            return True
        finally:
            self._lock.release()
    
    def _save_cookie_to_config(self, cookie: str):
        """保存 Cookie 到配置文件"""
        try:
            import yaml
            
            # 加载现有配置
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            
            # 更新 Cookie
            config.setdefault('monitor', {})['cookie'] = cookie
            
            # 保存配置
            os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            self.logger.info("Cookie 已保存到配置文件")
        except Exception as e:
            self.logger.error(f"保存 Cookie 到配置文件失败：{e}")
    
    def get_qrcode(self) -> tuple:
        """
        获取登录二维码
        
        Returns:
            (qrcode_url, qrcode_key): 二维码 URL 和密钥
            
        Raises:
            Exception: 获取二维码失败时抛出异常
        """
        if not self._api:
            self._api = BiliAPI(self.logger)
        
        url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        response = self._api.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 0:
            qrcode_url = data['data'].get('url', '')
            qrcode_key = data['data'].get('qrcode_key', '')
            if qrcode_url and qrcode_key:
                return (qrcode_url, qrcode_key)
            else:
                raise Exception("B站API返回数据缺少必要字段")
        else:
            error_msg = data.get('message', '未知错误')
            error_code = data.get('code', -1)
            raise Exception(f"B站API错误 [{error_code}]: {error_msg}")
    
    def check_login(self, qrcode_key: str) -> LoginStatus:
        """
        检查登录状态
        
        Args:
            qrcode_key: 二维码密钥
            
        Returns:
            LoginStatus: 登录状态
        """
        try:
            if not self._api:
                self._api = BiliAPI(self.logger)
            
            url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
            params = {'qrcode_key': qrcode_key}
            response = self._api.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('code') != 0:
                return LoginStatus(
                    success=False,
                    status=-1,
                    message=data.get('message', '请求失败')
                )
            
            login_data = data.get('data', {})
            status_code = login_data.get('code', -1)
            
            # 86101: 未扫码
            # 86090: 已扫码待确认
            # 86038: 二维码已过期
            # 0: 登录成功
            
            if status_code == 0:
                # 登录成功，提取 Cookie
                cookie_str = login_data.get('url', '')
                cookie = self._extract_cookie_from_url(cookie_str)
                
                if cookie:
                    # 获取用户信息
                    user_info = self._get_user_info(cookie)
                    
                    return LoginStatus(
                        success=True,
                        status=0,
                        message="登录成功",
                        cookie=cookie,
                        username=user_info.get('username'),
                        uid=user_info.get('uid')
                    )
                else:
                    return LoginStatus(
                        success=False,
                        status=-1,
                        message="未能提取到 Cookie"
                    )
            else:
                messages = {
                    86101: "未扫码",
                    86090: "已扫码待确认",
                    86038: "二维码已过期"
                }
                return LoginStatus(
                    success=False,
                    status=status_code,
                    message=messages.get(status_code, f"未知状态：{status_code}")
                )
        except Exception as e:
            self.logger.error(f"检查登录状态失败：{e}")
            return LoginStatus(
                success=False,
                status=-1,
                message=str(e)
            )
    
    def _extract_cookie_from_url(self, url: str) -> str:
        """从登录响应中提取 Cookie"""
        import urllib.parse
        
        cookies = []
        
        for cookie in self._api.session.cookies:
            cookies.append(f"{cookie.name}={cookie.value}")
        
        if cookies:
            return '; '.join(cookies)
        
        if 'gourl=' in url:
            try:
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                gourl = params.get('gourl', [''])[0]
                if gourl:
                    return urllib.parse.unquote(gourl)
            except:
                pass
        
        return ""
    
    def _get_user_info(self, cookie: str) -> Dict[str, Any]:
        """获取用户信息"""
        try:
            temp_api = BiliAPI(self.logger, cookie=cookie)
            response = temp_api.session.get(
                "https://api.bilibili.com/x/web-interface/nav",
                timeout=10
            )
            data = response.json()
            
            if data.get('code') == 0:
                user_data = data.get('data', {})
                return {
                    'username': user_data.get('uname', ''),
                    'uid': user_data.get('mid', 0)
                }
            return {}
        except Exception as e:
            self.logger.error(f"获取用户信息失败：{e}")
            return {}
    
    def close(self):
        """关闭服务"""
        self.stop_keepalive()
        if self._api:
            self._api.close()
        if self._cookie_manager:
            self._cookie_manager.close()


# 全局服务实例
_cookie_service: Optional[CookieService] = None


def get_cookie_service(config_path: str = "config.yaml") -> CookieService:
    """
    获取全局 Cookie 服务实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        CookieService: Cookie 服务实例
    """
    global _cookie_service
    
    if _cookie_service is None:
        # 从配置文件加载 Cookie
        cookie = ""
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    cookie = config.get('monitor', {}).get('cookie', '')
            except Exception:
                pass
        
        _cookie_service = CookieService(
            cookie=cookie,
            config_path=config_path
        )
    
    return _cookie_service


def check_cookie_status_standalone(cookie: str) -> Dict[str, Any]:
    """
    独立的 Cookie 状态检查函数（用于 Web API）
    
    Args:
        cookie: Cookie 字符串
        
    Returns:
        {'valid': bool, 'username': str}
    """
    if not cookie:
        return {'valid': False, 'username': None}
    
    try:
        validation = CookieValidator.validate(cookie)
        if not validation['valid']:
            return {'valid': False, 'username': None}
        
        # 快速检查 Cookie 有效性
        api = BiliAPI(logging.getLogger('bili-monitor'), cookie=cookie)
        try:
            response = api.session.get(
                "https://api.bilibili.com/x/web-interface/nav",
                timeout=5
            )
            data = response.json()
            
            if data.get('code') == 0:
                username = data.get('data', {}).get('uname', '已配置')
                return {'valid': True, 'username': username}
        except Exception:
            pass
        
        return {'valid': True, 'username': '已配置'}
    except Exception:
        return {'valid': False, 'username': None}
