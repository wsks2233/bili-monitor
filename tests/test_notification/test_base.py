"""通知模块测试"""

from __future__ import annotations

import pytest

from bili_monitor.api.endpoints import DynamicInfo, StatInfo
from bili_monitor.notification import create_notifier
from bili_monitor.notification.base import NotificationBase, NotificationResult


class TestNotificationResult:
    """NotificationResult 测试"""
    
    def test_default_timestamp(self) -> None:
        """测试默认时间戳"""
        result = NotificationResult(success=True, message="成功")
        assert result.timestamp != ""
    
    def test_custom_timestamp(self) -> None:
        """测试自定义时间戳"""
        result = NotificationResult(
            success=True,
            message="成功",
            timestamp="2024-01-01T00:00:00",
        )
        assert result.timestamp == "2024-01-01T00:00:00"


class TestNotificationBase:
    """NotificationBase 测试"""
    
    def test_format_message(self) -> None:
        """测试格式化消息"""
        # 创建一个简单的通知器实现
        class TestNotifier(NotificationBase):
            def send(self, dynamic: DynamicInfo) -> NotificationResult:
                return NotificationResult(success=True, message="OK")
            
            def test(self) -> bool:
                return True
        
        notifier = TestNotifier()
        dynamic = DynamicInfo(
            dynamic_id="12345",
            uid="12345",
            upstream_name="测试用户",
            dynamic_type="纯文字",
            content="测试内容",
            stat=StatInfo(like=100, repost=50, comment=20),
        )
        
        message = notifier.format_message(dynamic)
        assert "测试用户" in message
        assert "纯文字" in message
        assert "测试内容" in message
        assert "100" in message
        assert "12345" in message
    
    def test_format_simple_message(self) -> None:
        """测试格式化简化消息"""
        class TestNotifier(NotificationBase):
            def send(self, dynamic: DynamicInfo) -> NotificationResult:
                return NotificationResult(success=True, message="OK")
            
            def test(self) -> bool:
                return True
        
        notifier = TestNotifier()
        dynamic = DynamicInfo(
            dynamic_id="12345",
            uid="12345",
            upstream_name="测试用户",
            dynamic_type="纯文字",
            content="测试内容",
        )
        
        message = notifier.format_simple_message(dynamic)
        assert "测试用户" in message
        assert "纯文字" in message
        assert "12345" in message


class TestCreateNotifier:
    """create_notifier 测试"""
    
    def test_create_wechat(self) -> None:
        """测试创建企业微信通知器"""
        notifier = create_notifier("wechat", webhook_url="https://example.com")
        assert notifier.__class__.__name__ == "WeChatNotifier"
    
    def test_create_serverchan(self) -> None:
        """测试创建 Server酱通知器"""
        notifier = create_notifier("serverchan", serverchan_key="test_key")
        assert notifier.__class__.__name__ == "ServerChanNotifier"
    
    def test_create_pushplus(self) -> None:
        """测试创建 PushPlus 通知器"""
        notifier = create_notifier("pushplus", pushplus_token="test_token")
        assert notifier.__class__.__name__ == "PushPlusNotifier"
    
    def test_create_dingtalk(self) -> None:
        """测试创建钉钉通知器"""
        notifier = create_notifier("dingtalk", webhook_url="https://example.com")
        assert notifier.__class__.__name__ == "DingTalkNotifier"
    
    def test_create_email(self) -> None:
        """测试创建邮件通知器"""
        notifier = create_notifier(
            "email",
            smtp_server="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="password",
        )
        assert notifier.__class__.__name__ == "EmailNotifier"
    
    def test_create_telegram(self) -> None:
        """测试创建 Telegram 通知器"""
        notifier = create_notifier(
            "telegram",
            bot_token="test_token",
            chat_id="test_chat_id",
        )
        assert notifier.__class__.__name__ == "TelegramNotifier"
    
    def test_create_unknown(self) -> None:
        """测试创建未知类型通知器"""
        with pytest.raises(ValueError, match="不支持的通知类型"):
            create_notifier("unknown")
    
    def test_case_insensitive(self) -> None:
        """测试大小写不敏感"""
        notifier = create_notifier("WeChat", webhook_url="https://example.com")
        assert notifier.__class__.__name__ == "WeChatNotifier"


class TestNotificationHelpers:
    """_request() 和 _test_request() 辅助方法测试"""

    class _StubNotifier(NotificationBase):
        def send(self, dynamic: DynamicInfo) -> NotificationResult:
            return NotificationResult(success=True, message="OK")

        def test(self) -> bool:
            return True

    def _make_notifier(self) -> NotificationBase:
        return self._StubNotifier()

    def test_request_success_json(self, mocker) -> None:
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"code": 0, "message": "ok"}
        mocker.patch("bili_monitor.notification.base.requests.post", return_value=mock_resp)

        notifier = self._make_notifier()
        result = notifier._request("POST", "http://example.com", "code", 0, "成功", "测试")
        assert result.success is True
        assert "成功" in result.message

    def test_request_success_form(self, mocker) -> None:
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"code": 0}
        mocker.patch("bili_monitor.notification.base.requests.post", return_value=mock_resp)

        notifier = self._make_notifier()
        result = notifier._request("POST", "http://example.com", "code", 0, "成功", "测试", form_data={"key": "val"})
        assert result.success is True

    def test_request_failure(self, mocker) -> None:
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"code": -1, "message": "error"}
        mocker.patch("bili_monitor.notification.base.requests.post", return_value=mock_resp)

        notifier = self._make_notifier()
        result = notifier._request("POST", "http://example.com", "code", 0, "成功", "测试")
        assert result.success is False
        assert "失败" in result.message

    def test_request_exception(self, mocker) -> None:
        mocker.patch("bili_monitor.notification.base.requests.post", side_effect=Exception("connection error"))

        notifier = self._make_notifier()
        result = notifier._request("POST", "http://example.com", "code", 0, "成功", "测试")
        assert result.success is False
        assert "异常" in result.message

    def test_test_request_success(self, mocker) -> None:
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"ok": True}
        mocker.patch("bili_monitor.notification.base.requests.post", return_value=mock_resp)

        notifier = self._make_notifier()
        assert notifier._test_request("POST", "http://example.com", "ok", True, payload={"text": "hi"}) is True

    def test_test_request_failure(self, mocker) -> None:
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"ok": False}
        mocker.patch("bili_monitor.notification.base.requests.post", return_value=mock_resp)

        notifier = self._make_notifier()
        assert notifier._test_request("POST", "http://example.com", "ok", True) is False

    def test_test_request_exception(self, mocker) -> None:
        mocker.patch("bili_monitor.notification.base.requests.post", side_effect=Exception("timeout"))

        notifier = self._make_notifier()
        assert notifier._test_request("POST", "http://example.com", "ok", True) is False
