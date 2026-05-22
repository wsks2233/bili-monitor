"""WBI 签名器测试"""

from __future__ import annotations

import time

import pytest

from bili_monitor.api.wbi import WBISigner


class TestWBISigner:
    """WBISigner 测试"""
    
    def test_initial_state(self) -> None:
        """测试初始状态"""
        signer = WBISigner()
        assert signer.is_valid is False
    
    def test_update_keys(self) -> None:
        """测试更新密钥"""
        signer = WBISigner()
        signer.update_keys("test_img_key", "test_sub_key")
        assert signer.is_valid is True
        assert signer._img_key == "test_img_key"
        assert signer._sub_key == "test_sub_key"
    
    def test_keys_expire(self) -> None:
        """测试密钥过期"""
        signer = WBISigner()
        signer._ttl = 0  # 立即过期
        signer.update_keys("test_img_key", "test_sub_key")
        time.sleep(0.1)
        assert signer.is_valid is False
    
    def test_get_mixin_key(self) -> None:
        """测试获取混淆密钥"""
        signer = WBISigner()
        # 需要至少 64 个字符的字符串（MIXIN_KEY_ENC_TAB 最大索引是 63）
        test_str = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl"
        key = signer.get_mixin_key(test_str)
        assert len(key) == 32
    
    def test_sign_without_keys(self) -> None:
        """测试无密钥时签名"""
        signer = WBISigner()
        params = {"mid": "12345"}
        result = signer.sign(params)
        # 无密钥时返回原始参数
        assert result == params
    
    def test_sign_with_keys(self) -> None:
        """测试有密钥时签名"""
        signer = WBISigner()
        # 使用足够长的密钥（至少 64 个字符）
        signer.update_keys(
            "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOP",
            "QRSTUVWXYZabcdefghijklmn0123456789ABCDEFGHIJKLMN",
        )
        
        params = {"mid": "12345"}
        result = signer.sign(params)
        
        # 应该添加 wts 和 w_rid
        assert "wts" in result
        assert "w_rid" in result
        assert result["mid"] == "12345"
        assert len(result["w_rid"]) == 32  # MD5 哈希长度
    
    def test_sign_params_sorted(self) -> None:
        """测试签名参数排序"""
        signer = WBISigner()
        # 使用足够长的密钥（至少 64 个字符）
        signer.update_keys(
            "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOP",
            "QRSTUVWXYZabcdefghijklmn0123456789ABCDEFGHIJKLMN",
        )
        
        params = {"z": "1", "a": "2", "m": "3"}
        result = signer.sign(params)
        
        # 参数应该被排序
        assert "wts" in result
        assert "w_rid" in result
