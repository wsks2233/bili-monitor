# -*- coding: utf-8 -*-
"""
B站Cookie保活管理器

功能：
1. Cookie有效性检测
2. 自动保活（通过定期访问保持Session活跃）
3. 过期预警通知
4. 安全的请求策略

风控原则：
- 控制请求频率，模拟正常用户行为
- 避免敏感操作（如频繁登录、修改信息等）
- 使用合理的User-Agent和请求头
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict
import requests
import threading


@dataclass
class CookieStatus:
    is_valid: bool
    uid: int
    username: str
    vip_status: int
    is_login: bool
    check_time: str
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _mask_username(name: str) -> str:
    if not name or len(name) <= 2:
        return name[0] + '*' if name else ''
    return name[0] + '*' * (len(name) - 2) + name[-1]


class CookieManager:
    """
    Cookie保活管理器
    
    使用方法：
    ```python
    manager = CookieManager(cookie="你的Cookie")
    
    # 检查Cookie状态
    status = manager.check_cookie_status()
    print(f"登录状态: {status.is_valid}, 用户: {status.username}")
    
    # 启动后台保活线程
    manager.start_keepalive()
    
    # 设置过期回调
    manager.on_expired = lambda status: print("Cookie已过期！")
    ```
    """
    
    NAV_API = "https://api.bilibili.com/x/web-interface/nav"
    HOME_URL = "https://www.bilibili.com/"
    SPACE_URL = "https://space.bilibili.com/{}/dynamic"
    
    def __init__(
        self,
        cookie: str,
        logger: Optional[logging.Logger] = None,
        config_path: str = "data/cookie_status.json",
        check_interval: int = 3600,  # 检查间隔（秒）
        keepalive_interval: int = 1800,  # 保活间隔（秒）
        min_request_interval: float = 2.0,  # 最小请求间隔
    ):
        self.cookie = cookie
        self.logger = logger or logging.getLogger('bili-monitor')
        self.config_path = config_path
        self.check_interval = check_interval
        self.keepalive_interval = keepalive_interval
        self.min_request_interval = min_request_interval
        
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': cookie,
        })
        
        self._last_request_time = 0
        self._running = False
        self._keepalive_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.on_expired: Optional[Callable[[CookieStatus], None]] = None
        self.on_expiring: Optional[Callable[[CookieStatus, int], None]] = None  # 即将过期回调
        
        # 加载历史状态
        self._status_history: list = []
        self._load_status()
    
    def _load_status(self):
        """加载历史状态"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._status_history = data.get('history', [])
            except Exception as e:
                self.logger.warning(f"加载Cookie状态历史失败: {e}")
    
    def _save_status(self):
        """保存状态历史"""
        os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'history': self._status_history[-100:],  # 只保留最近100条
                    'updated_at': datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"保存Cookie状态失败: {e}")
    
    def _wait_for_rate_limit(self):
        """等待以避免触发频率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed + 0.5)
        self._last_request_time = time.time()
    
    def check_cookie_status(self) -> CookieStatus:
        """
        检查Cookie状态
        
        Returns:
            CookieStatus: Cookie状态信息
        """
        self._wait_for_rate_limit()
        
        try:
            response = self._session.get(self.NAV_API, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                user_data = data.get('data', {})
                status = CookieStatus(
                    is_valid=True,
                    uid=user_data.get('mid', 0),
                    username=user_data.get('uname', ''),
                    vip_status=user_data.get('vipStatus', 0),
                    is_login=user_data.get('isLogin', False),
                    check_time=datetime.now().isoformat(),
                    message="Cookie有效"
                )
            else:
                status = CookieStatus(
                    is_valid=False,
                    uid=0,
                    username='',
                    vip_status=0,
                    is_login=False,
                    check_time=datetime.now().isoformat(),
                    message=data.get('message', '未知错误')
                )
            
            # 记录状态
            self._status_history.append(status.to_dict())
            self._save_status()
            
            # 触发回调
            if not status.is_valid and self.on_expired:
                self.on_expired(status)
            
            return status
            
        except Exception as e:
            self.logger.error(f"检查Cookie状态失败: {e}")
            return CookieStatus(
                is_valid=False,
                uid=0,
                username='',
                vip_status=0,
                is_login=False,
                check_time=datetime.now().isoformat(),
                message=str(e)
            )
    
    def keepalive(self) -> bool:
        """
        保活操作 - 通过访问B站页面保持Session活跃
        
        策略：
        1. 访问B站首页
        2. 访问用户空间（如果有UID）
        
        Returns:
            bool: 保活是否成功
        """
        self.logger.info("执行Cookie保活...")
        
        try:
            # 1. 访问首页
            self._wait_for_rate_limit()
            response = self._session.get(self.HOME_URL, timeout=30)
            if response.status_code != 200:
                self.logger.warning(f"访问首页失败: {response.status_code}")
            
            # 2. 检查登录状态
            status = self.check_cookie_status()
            
            if status.is_valid:
                self.logger.info(f"Cookie保活成功: {_mask_username(status.username)}")
                
                # 3. 访问用户空间（模拟正常用户行为）
                if status.uid:
                    self._wait_for_rate_limit()
                    space_url = self.SPACE_URL.format(status.uid)
                    self._session.get(space_url, timeout=30)
                
                return True
            else:
                self.logger.warning(f"Cookie已失效: {status.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"保活失败: {e}")
            return False
    
    def _keepalive_loop(self):
        """保活循环（后台线程）"""
        while self._running:
            try:
                # 执行保活
                self.keepalive()
                
                # 等待下次保活
                for _ in range(self.keepalive_interval):
                    if not self._running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"保活循环异常: {e}")
                time.sleep(60)
    
    def start_keepalive(self):
        """启动后台保活线程"""
        if self._running:
            self.logger.warning("保活线程已在运行")
            return
        
        self._running = True
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop,
            daemon=True,
            name="CookieKeepalive"
        )
        self._keepalive_thread.start()
        self.logger.info("Cookie保活线程已启动")
    
    def stop_keepalive(self):
        """停止保活线程"""
        self._running = False
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=5)
        self.logger.info("Cookie保活线程已停止")
    
    def get_remaining_days(self) -> Optional[int]:
        """
        估算Cookie剩余有效天数
        
        注意：这只是估算，实际有效期取决于B站服务端设置
        
        Returns:
            Optional[int]: 剩余天数，无法估算时返回None
        """
        # B站SESSDATA通常有效期为30天左右
        # 通过历史检查记录估算
        if len(self._status_history) < 2:
            return None
        
        # 简单估算：假设从首次检查开始计算
        first_check = self._status_history[0].get('check_time', '')
        if not first_check:
            return None
        
        try:
            first_time = datetime.fromisoformat(first_check)
            elapsed_days = (datetime.now() - first_time).days
            # 假设有效期30天
            remaining = max(0, 30 - elapsed_days)
            return remaining
        except:
            return None
    
    def update_cookie(self, new_cookie: str):
        """
        更新Cookie
        
        Args:
            new_cookie: 新的Cookie字符串
        """
        self.cookie = new_cookie
        self._session.headers['Cookie'] = new_cookie
        self._status_history = []  # 清空历史
        self._save_status()
        self.logger.info("Cookie已更新")
    
    def close(self):
        """关闭管理器"""
        self.stop_keepalive()
        self._session.close()


class CookieValidator:
    """
    Cookie验证工具
    
    用于验证Cookie格式和必要字段
    """
    
    LOGIN_REQUIRED_FIELDS = ['SESSDATA', 'bili_jct', 'DedeUserID']
    RECOMMENDED_FIELDS = ['buvid3', 'buvid4', 'sid']
    
    @classmethod
    def parse_cookie(cls, cookie: str) -> Dict[str, str]:
        """解析Cookie字符串为字典"""
        result = {}
        for item in cookie.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                result[key.strip()] = value.strip()
        return result
    
    @classmethod
    def validate(cls, cookie: str, require_login: bool = False) -> Dict[str, Any]:
        """
        验证Cookie
        
        Args:
            cookie: Cookie字符串
            require_login: 是否要求登录态Cookie
            
        Returns:
            {
                'valid': bool,
                'has_login': bool,
                'missing_required': list,
                'missing_recommended': list,
                'message': str
            }
        """
        cookie_dict = cls.parse_cookie(cookie)
        
        has_login = all(f in cookie_dict for f in cls.LOGIN_REQUIRED_FIELDS)
        missing_login = [f for f in cls.LOGIN_REQUIRED_FIELDS if f not in cookie_dict]
        missing_recommended = [f for f in cls.RECOMMENDED_FIELDS if f not in cookie_dict]
        
        if require_login and not has_login:
            return {
                'valid': False,
                'has_login': False,
                'missing_required': missing_login,
                'missing_recommended': missing_recommended,
                'message': f"缺少登录必要字段: {', '.join(missing_login)}"
            }
        
        if not cookie_dict:
            return {
                'valid': False,
                'has_login': False,
                'missing_required': cls.LOGIN_REQUIRED_FIELDS,
                'missing_recommended': cls.RECOMMENDED_FIELDS,
                'message': "Cookie为空"
            }
        
        message = "Cookie格式有效"
        if has_login:
            message += "（含登录态）"
        else:
            message += f"（仅设备标识，缺少登录字段: {', '.join(missing_login)}）"
        if missing_recommended:
            message += f"，建议添加: {', '.join(missing_recommended)}"
        
        return {
            'valid': True,
            'has_login': has_login,
            'missing_required': missing_login,
            'missing_recommended': missing_recommended,
            'message': message
        }
    
    @classmethod
    def extract_sessdata(cls, cookie: str) -> Optional[str]:
        """提取SESSDATA"""
        cookie_dict = cls.parse_cookie(cookie)
        return cookie_dict.get('SESSDATA')
