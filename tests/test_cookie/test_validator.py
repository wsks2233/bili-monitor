"""Cookie 验证器测试"""

from __future__ import annotations

import pytest

from bili_monitor.cookie.validator import CookieValidator


class TestCookieValidator:
    """CookieValidator 测试"""
    
    def test_parse_cookie_empty(self) -> None:
        """测试解析空 Cookie"""
        result = CookieValidator.parse_cookie("")
        assert result == {}
    
    def test_parse_cookie_single(self) -> None:
        """测试解析单个 Cookie"""
        result = CookieValidator.parse_cookie("SESSDATA=abc123")
        assert result == {"SESSDATA": "abc123"}
    
    def test_parse_cookie_multiple(self) -> None:
        """测试解析多个 Cookie"""
        cookie = "SESSDATA=abc123; bili_jct=def456; DedeUserID=789"
        result = CookieValidator.parse_cookie(cookie)
        assert result == {
            "SESSDATA": "abc123",
            "bili_jct": "def456",
            "DedeUserID": "789",
        }
    
    def test_parse_cookie_with_spaces(self) -> None:
        """测试解析带空格的 Cookie"""
        cookie = "SESSDATA=abc123 ; bili_jct=def456"
        result = CookieValidator.parse_cookie(cookie)
        assert result == {
            "SESSDATA": "abc123",
            "bili_jct": "def456",
        }
    
    def test_validate_empty_cookie(self) -> None:
        """测试验证空 Cookie"""
        result = CookieValidator.validate("")
        assert result["valid"] is False
        assert result["has_login"] is False
        assert "Cookie 为空" in result["message"]
    
    def test_validate_valid_cookie_with_login(self) -> None:
        """测试验证有效 Cookie（含登录态）"""
        cookie = "SESSDATA=abc123; bili_jct=def456; DedeUserID=789"
        result = CookieValidator.validate(cookie)
        assert result["valid"] is True
        assert result["has_login"] is True
        assert "含登录态" in result["message"]
    
    def test_validate_valid_cookie_without_login(self) -> None:
        """测试验证有效 Cookie（不含登录态）"""
        cookie = "buvid3=abc123"
        result = CookieValidator.validate(cookie)
        assert result["valid"] is True
        assert result["has_login"] is False
        assert "仅设备标识" in result["message"]
    
    def test_validate_require_login_missing(self) -> None:
        """测试要求登录态但缺少"""
        cookie = "buvid3=abc123"
        result = CookieValidator.validate(cookie, require_login=True)
        assert result["valid"] is False
        assert result["has_login"] is False
        assert "缺少登录必要字段" in result["message"]
    
    def test_validate_require_login_present(self) -> None:
        """测试要求登录态且存在"""
        cookie = "SESSDATA=abc123; bili_jct=def456; DedeUserID=789"
        result = CookieValidator.validate(cookie, require_login=True)
        assert result["valid"] is True
        assert result["has_login"] is True
    
    def test_extract_sessdata(self) -> None:
        """测试提取 SESSDATA"""
        cookie = "SESSDATA=abc123; bili_jct=def456"
        result = CookieValidator.extract_sessdata(cookie)
        assert result == "abc123"
    
    def test_extract_sessdata_missing(self) -> None:
        """测试提取 SESSDATA（不存在）"""
        cookie = "buvid3=abc123"
        result = CookieValidator.extract_sessdata(cookie)
        assert result is None
