"""配置模块测试"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from bili_monitor.config.loader import load_config, save_config
from bili_monitor.config.models import AppConfig, MonitorConfig, UpstreamConfig


class TestAppConfig:
    """AppConfig 测试"""
    
    def test_from_dict_empty(self) -> None:
        """测试从空字典创建配置"""
        config = AppConfig.from_dict({})
        assert config.monitor.check_interval == 300
        assert config.upstreams == []
        assert config.logger.level == "INFO"
    
    def test_from_dict_with_data(self) -> None:
        """测试从字典创建配置"""
        data = {
            "monitor": {
                "check_interval": 600,
                "cookie": "test_cookie",
            },
            "upstreams": [
                {"uid": "12345", "name": "测试用户"},
            ],
            "logger": {
                "level": "DEBUG",
            },
        }
        config = AppConfig.from_dict(data)
        assert config.monitor.check_interval == 600
        assert config.monitor.cookie == "test_cookie"
        assert len(config.upstreams) == 1
        assert config.upstreams[0].uid == "12345"
        assert config.logger.level == "DEBUG"


class TestLoadConfig:
    """load_config 测试"""
    
    def test_load_nonexistent_file(self) -> None:
        """测试加载不存在的文件"""
        with pytest.raises(Exception):
            load_config("nonexistent.yaml")
    
    def test_load_and_save(self) -> None:
        """测试加载和保存配置"""
        import os
        
        config = AppConfig(
            monitor=MonitorConfig(check_interval=600),
            upstreams=[UpstreamConfig(uid="12345", name="测试")],
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            save_config(config, temp_path)
            loaded = load_config(temp_path)
            assert loaded.monitor.check_interval == 600
            assert len(loaded.upstreams) == 1
            assert loaded.upstreams[0].uid == "12345"
        finally:
            Path(temp_path).unlink(missing_ok=True)
