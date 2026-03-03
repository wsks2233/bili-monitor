# -*- coding: utf-8 -*-
"""
B站扫码登录模块

实现扫码登录功能，用户只需用B站App扫码即可自动获取Cookie
"""

import logging
import time
import requests
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class QRCodeStatus:
    status: int
    message: str
    cookie: str = ""
    url: str = ""
    qrcode_key: str = ""


class BiliLogin:
    """
    B站扫码登录
    
    使用方法：
    ```python
    login = BiliLogin()
    
    # 获取二维码
    qrcode_url, qrcode_key = login.get_qrcode()
    
    # 轮询检查扫码状态
    while True:
        status = login.check_scan(qrcode_key)
        if status.status == 0:  # 扫码成功
            print(f"Cookie: {status.cookie}")
            break
        time.sleep(2)
    ```
    """
    
    QRCODE_GENERATE_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    QRCODE_POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    NAV_URL = "https://api.bilibili.com/x/web-interface/nav"
    
    STATUS_MAP = {
        0: "扫码成功",
        86038: "二维码已失效",
        86090: "已扫码未确认",
        86101: "未扫码",
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('bili-monitor.login')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://passport.bilibili.com',
            'Referer': 'https://passport.bilibili.com/',
        })
    
    def get_qrcode(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取登录二维码
        
        Returns:
            Tuple[str, str]: (二维码URL, qrcode_key)
        """
        try:
            response = self.session.get(self.QRCODE_GENERATE_URL, timeout=10)
            data = response.json()
            
            if data.get('code') == 0:
                result = data.get('data', {})
                qrcode_url = result.get('url', '')
                qrcode_key = result.get('qrcode_key', '')
                self.logger.info(f"获取二维码成功: {qrcode_key}")
                return qrcode_url, qrcode_key
            else:
                self.logger.error(f"获取二维码失败: {data.get('message')}")
                return None, None
                
        except Exception as e:
            self.logger.error(f"获取二维码异常: {e}")
            return None, None
    
    def check_scan(self, qrcode_key: str) -> QRCodeStatus:
        """
        检查扫码状态
        
        Args:
            qrcode_key: 二维码key
            
        Returns:
            QRCodeStatus: 扫码状态
        """
        try:
            response = self.session.get(
                self.QRCODE_POLL_URL,
                params={'qrcode_key': qrcode_key},
                timeout=10
            )
            data = response.json()
            
            code = data.get('data', {}).get('code', -1)
            message = self.STATUS_MAP.get(code, data.get('message', '未知状态'))
            
            if code == 0:
                cookie = self._extract_cookie(response)
                url = data.get('data', {}).get('url', '')
                self.logger.info("扫码登录成功")
                return QRCodeStatus(
                    status=0,
                    message="登录成功",
                    cookie=cookie,
                    url=url,
                    qrcode_key=qrcode_key
                )
            else:
                return QRCodeStatus(
                    status=code,
                    message=message,
                    qrcode_key=qrcode_key
                )
                
        except Exception as e:
            self.logger.error(f"检查扫码状态异常: {e}")
            return QRCodeStatus(status=-1, message=str(e))
    
    def _extract_cookie(self, response: requests.Response) -> str:
        """
        从响应中提取Cookie
        """
        cookies = []
        
        for cookie in self.session.cookies:
            cookies.append(f"{cookie.name}={cookie.value}")
        
        set_cookie_headers = response.headers.get('Set-Cookie', '')
        if set_cookie_headers:
            pass
        
        return '; '.join(cookies)
    
    def verify_cookie(self, cookie: str) -> Dict[str, Any]:
        """
        验证Cookie有效性
        
        Args:
            cookie: Cookie字符串
            
        Returns:
            Dict: 验证结果
        """
        try:
            headers = {
                'Cookie': cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            response = requests.get(self.NAV_URL, headers=headers, timeout=10)
            data = response.json()
            
            if data.get('code') == 0:
                user_data = data.get('data', {})
                return {
                    'valid': True,
                    'uid': user_data.get('mid'),
                    'username': user_data.get('uname'),
                    'vip': user_data.get('vipStatus', 0) == 1,
                }
            else:
                return {
                    'valid': False,
                    'message': data.get('message', '验证失败')
                }
                
        except Exception as e:
            return {
                'valid': False,
                'message': str(e)
            }
    
    def close(self):
        self.session.close()
