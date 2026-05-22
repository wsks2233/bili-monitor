"""Cookie 验证器"""

from __future__ import annotations

from typing import Any


class CookieValidator:
    """Cookie 验证工具"""
    
    LOGIN_REQUIRED_FIELDS = ["SESSDATA", "bili_jct", "DedeUserID"]
    RECOMMENDED_FIELDS = ["buvid3", "buvid4", "sid"]
    
    @classmethod
    def parse_cookie(cls, cookie: str) -> dict[str, str]:
        """解析 Cookie 字符串为字典"""
        result = {}
        for item in cookie.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                result[key.strip()] = value.strip()
        return result
    
    @classmethod
    def validate(cls, cookie: str, require_login: bool = False) -> dict[str, Any]:
        """验证 Cookie
        
        Args:
            cookie: Cookie 字符串
            require_login: 是否要求登录态
            
        Returns:
            验证结果
        """
        cookie_dict = cls.parse_cookie(cookie)
        
        has_login = all(f in cookie_dict for f in cls.LOGIN_REQUIRED_FIELDS)
        missing_login = [f for f in cls.LOGIN_REQUIRED_FIELDS if f not in cookie_dict]
        missing_recommended = [f for f in cls.RECOMMENDED_FIELDS if f not in cookie_dict]
        
        if require_login and not has_login:
            return {
                "valid": False,
                "has_login": False,
                "missing_required": missing_login,
                "missing_recommended": missing_recommended,
                "message": f"缺少登录必要字段: {', '.join(missing_login)}",
            }
        
        if not cookie_dict:
            return {
                "valid": False,
                "has_login": False,
                "missing_required": cls.LOGIN_REQUIRED_FIELDS,
                "missing_recommended": cls.RECOMMENDED_FIELDS,
                "message": "Cookie 为空",
            }
        
        message = "Cookie 格式有效"
        if has_login:
            message += "（含登录态）"
        else:
            message += f"（仅设备标识，缺少登录字段: {', '.join(missing_login)}）"
        if missing_recommended:
            message += f"，建议添加: {', '.join(missing_recommended)}"
        
        return {
            "valid": True,
            "has_login": has_login,
            "missing_required": missing_login,
            "missing_recommended": missing_recommended,
            "message": message,
        }
    
    @classmethod
    def extract_sessdata(cls, cookie: str) -> str | None:
        """提取 SESSDATA"""
        cookie_dict = cls.parse_cookie(cookie)
        return cookie_dict.get("SESSDATA")
