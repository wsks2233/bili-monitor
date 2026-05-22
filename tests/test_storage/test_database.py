"""数据库测试"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from bili_monitor.api.endpoints import DynamicInfo, ImageInfo, StatInfo, UpstreamInfo, VideoInfo
from bili_monitor.config.models import DatabaseConfig
from bili_monitor.storage.database import Database


@pytest.fixture
def temp_db() -> Database:
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    config = DatabaseConfig(path=db_path)
    db = Database(config)
    yield db
    db.close()
    Path(db_path).unlink(missing_ok=True)


class TestDatabase:
    """数据库测试"""
    
    def test_init_tables(self, temp_db: Database) -> None:
        """测试初始化表"""
        # 表应该已经创建
        cursor = temp_db._conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "dynamics" in tables
        assert "upstreams" in tables
        assert "state" in tables
    
    def test_save_upstream(self, temp_db: Database) -> None:
        """测试保存 UP 主信息"""
        upstream = UpstreamInfo(
            uid="12345",
            name="测试用户",
            face="http://example.com/face.jpg",
            sign="测试签名",
            level=6,
            fans=10000,
        )
        result = temp_db.save_upstream(upstream)
        assert result is True
    
    def test_get_upstream(self, temp_db: Database) -> None:
        """测试获取 UP 主信息"""
        # 保存
        upstream = UpstreamInfo(uid="12345", name="测试用户")
        temp_db.save_upstream(upstream)
        
        # 获取
        result = temp_db.get_upstream("12345")
        assert result is not None
        assert result.uid == "12345"
        assert result.name == "测试用户"
    
    def test_get_upstream_not_found(self, temp_db: Database) -> None:
        """测试获取不存在的 UP 主"""
        result = temp_db.get_upstream("99999")
        assert result is None
    
    def test_save_dynamic(self, temp_db: Database) -> None:
        """测试保存动态"""
        dynamic = DynamicInfo(
            dynamic_id="test_dynamic_001",
            uid="12345",
            upstream_name="测试用户",
            dynamic_type="纯文字",
            content="这是一条测试动态",
            publish_time=datetime.now(),
            stat=StatInfo(like=100, repost=50, comment=20),
        )
        result = temp_db.save_dynamic(dynamic)
        assert result is True
    
    def test_save_dynamic_duplicate(self, temp_db: Database) -> None:
        """测试保存重复动态"""
        dynamic = DynamicInfo(
            dynamic_id="test_dynamic_001",
            uid="12345",
            upstream_name="测试用户",
            dynamic_type="纯文字",
            content="这是一条测试动态",
        )
        
        # 第一次保存
        result1 = temp_db.save_dynamic(dynamic)
        assert result1 is True
        
        # 第二次保存（应该返回 False）
        result2 = temp_db.save_dynamic(dynamic)
        assert result2 is False
    
    def test_dynamic_exists(self, temp_db: Database) -> None:
        """测试检查动态是否存在"""
        dynamic = DynamicInfo(
            dynamic_id="test_dynamic_001",
            uid="12345",
            upstream_name="测试用户",
        )
        temp_db.save_dynamic(dynamic)
        
        assert temp_db.dynamic_exists("test_dynamic_001") is True
        assert temp_db.dynamic_exists("nonexistent") is False
    
    def test_get_processed_ids(self, temp_db: Database) -> None:
        """测试获取已处理的动态 ID"""
        # 保存多个动态
        for i in range(5):
            dynamic = DynamicInfo(
                dynamic_id=f"test_dynamic_{i:03d}",
                uid="12345",
                upstream_name="测试用户",
            )
            temp_db.save_dynamic(dynamic)
        
        # 获取已处理的 ID
        ids = temp_db.get_processed_ids("12345")
        assert len(ids) == 5
        assert "test_dynamic_000" in ids
        assert "test_dynamic_004" in ids
    
    def test_get_dynamics(self, temp_db: Database) -> None:
        """测试获取动态列表"""
        # 保存动态
        dynamic = DynamicInfo(
            dynamic_id="test_dynamic_001",
            uid="12345",
            upstream_name="测试用户",
            dynamic_type="纯文字",
            content="测试内容",
            publish_time=datetime.now(),
            stat=StatInfo(like=100, repost=50, comment=20),
        )
        temp_db.save_dynamic(dynamic)
        
        # 获取动态列表
        dynamics = temp_db.get_dynamics(uid="12345")
        assert len(dynamics) == 1
        assert dynamics[0]["dynamic_id"] == "test_dynamic_001"
        assert dynamics[0]["like_count"] == 100
    
    def test_get_stats(self, temp_db: Database) -> None:
        """测试获取统计信息"""
        # 保存数据
        upstream = UpstreamInfo(uid="12345", name="测试用户")
        temp_db.save_upstream(upstream)
        
        dynamic = DynamicInfo(
            dynamic_id="test_dynamic_001",
            uid="12345",
            upstream_name="测试用户",
        )
        temp_db.save_dynamic(dynamic)
        
        # 获取统计
        stats = temp_db.get_stats()
        assert stats["total_dynamics"] == 1
        assert stats["total_upstreams"] == 1
        assert len(stats["upstream_stats"]) == 1
        assert stats["upstream_stats"][0]["count"] == 1
