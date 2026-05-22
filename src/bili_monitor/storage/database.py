"""数据库存储层

SQLite 数据库操作，包含：
- 动态存储
- UP主信息存储
- 状态管理
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ..api.endpoints import DynamicInfo, UpstreamInfo
from ..config.models import DatabaseConfig


class DatabaseError(Exception):
    """数据库错误"""


class Database:
    """SQLite 数据库
    
    使用示例：
        db = Database(DatabaseConfig(path="data/bili_monitor.db"))
        db.save_dynamic(dynamic)
        db.close()
    """
    
    def __init__(
        self,
        config: DatabaseConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger("bili-monitor.storage")
        self._conn: sqlite3.Connection | None = None
        self._init_connection()
    
    def _init_connection(self) -> None:
        """初始化数据库连接"""
        db_path = Path(self._config.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._logger.info(f"SQLite 数据库连接成功: {self._config.path}")
        self._init_tables()
    
    def _init_tables(self) -> None:
        """初始化数据库表"""
        cursor = self._conn.cursor()
        
        # 动态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dynamics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dynamic_id TEXT UNIQUE NOT NULL,
                uid TEXT NOT NULL,
                upstream_name TEXT,
                dynamic_type TEXT,
                content TEXT,
                publish_time TIMESTAMP,
                create_time TIMESTAMP,
                images TEXT,
                video TEXT,
                stat_like INTEGER DEFAULT 0,
                stat_repost INTEGER DEFAULT 0,
                stat_comment INTEGER DEFAULT 0,
                raw_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dynamics_uid ON dynamics(uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dynamics_publish_time ON dynamics(publish_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dynamics_dynamic_id ON dynamics(dynamic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dynamics_uid_publish ON dynamics(uid, publish_time DESC)")
        
        # UP主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upstreams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                name TEXT,
                face TEXT,
                sign TEXT,
                level INTEGER DEFAULT 0,
                fans INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 状态表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self._conn.commit()
        self._logger.info("数据库表初始化完成")
    
    def save_dynamic(self, dynamic: DynamicInfo) -> bool:
        """保存动态（仅插入，不更新已有记录）
        
        Args:
            dynamic: 动态信息
            
        Returns:
            是否是新记录
        """
        try:
            cursor = self._conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                "SELECT 1 FROM dynamics WHERE dynamic_id = ?",
                (dynamic.dynamic_id,),
            )
            if cursor.fetchone():
                self._logger.debug(f"动态已存在，跳过: {dynamic.dynamic_id}")
                return False
            
            # 序列化数据
            images_json = json.dumps(
                [img.to_dict() for img in dynamic.images],
                ensure_ascii=False,
            )
            video_json = (
                json.dumps(dynamic.video.to_dict(), ensure_ascii=False)
                if dynamic.video
                else None
            )
            raw_json = (
                json.dumps(dynamic.raw_json, ensure_ascii=False)
                if dynamic.raw_json
                else None
            )
            
            cursor.execute(
                """
                INSERT INTO dynamics 
                (dynamic_id, uid, upstream_name, dynamic_type, content, 
                 publish_time, create_time, images, video, 
                 stat_like, stat_repost, stat_comment, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dynamic.dynamic_id,
                    dynamic.uid,
                    dynamic.upstream_name,
                    dynamic.dynamic_type,
                    dynamic.content,
                    dynamic.publish_time.isoformat() if dynamic.publish_time else None,
                    dynamic.create_time.isoformat() if dynamic.create_time else None,
                    images_json,
                    video_json,
                    dynamic.stat.like,
                    dynamic.stat.repost,
                    dynamic.stat.comment,
                    raw_json,
                    datetime.now().isoformat(),
                ),
            )
            
            self._conn.commit()
            self._logger.debug(f"保存动态成功: {dynamic.dynamic_id}")
            return True
        except Exception as e:
            self._logger.error(f"保存动态失败: {e}")
            self._conn.rollback()
            return False
    
    def dynamic_exists(self, dynamic_id: str) -> bool:
        """检查动态是否存在"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM dynamics WHERE dynamic_id = ?", (dynamic_id,))
        return cursor.fetchone() is not None
    
    def get_processed_ids(self, uid: str, limit: int = 100) -> set[str]:
        """获取已处理的动态 ID 列表"""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT dynamic_id FROM dynamics 
            WHERE uid = ? 
            ORDER BY publish_time DESC 
            LIMIT ?
            """,
            (uid, limit),
        )
        return {row["dynamic_id"] for row in cursor.fetchall()}
    
    def save_upstream(self, upstream: UpstreamInfo) -> bool:
        """保存 UP 主信息"""
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO upstreams 
                (uid, name, face, sign, level, fans, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upstream.uid,
                    upstream.name,
                    upstream.face,
                    upstream.sign,
                    upstream.level,
                    upstream.fans,
                    datetime.now().isoformat(),
                ),
            )
            self._conn.commit()
            self._logger.debug(f"保存 UP 主信息成功: {upstream.uid}")
            return True
        except Exception as e:
            self._logger.error(f"保存 UP 主信息失败: {e}")
            self._conn.rollback()
            return False
    
    def get_upstream(self, uid: str) -> UpstreamInfo | None:
        """获取 UP 主信息"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM upstreams WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if row:
            return UpstreamInfo(
                uid=row["uid"],
                name=row["name"],
                face=row["face"],
                sign=row["sign"],
                level=row["level"],
                fans=row["fans"],
            )
        return None
    
    def get_dynamics(
        self,
        uid: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """获取动态列表"""
        cursor = self._conn.cursor()
        
        if uid:
            cursor.execute(
                """
                SELECT dynamic_id, uid, upstream_name, dynamic_type, content, 
                       publish_time, create_time, images, video, 
                       stat_like, stat_repost, stat_comment
                FROM dynamics 
                WHERE uid = ? 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
                """,
                (uid, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT dynamic_id, uid, upstream_name, dynamic_type, content, 
                       publish_time, create_time, images, video, 
                       stat_like, stat_repost, stat_comment
                FROM dynamics 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            row_dict = dict(row)
            row_dict["like_count"] = row_dict.pop("stat_like", 0)
            row_dict["repost_count"] = row_dict.pop("stat_repost", 0)
            row_dict["comment_count"] = row_dict.pop("stat_comment", 0)
            
            # 解析图片
            if row_dict.get("images"):
                try:
                    images_data = json.loads(row_dict["images"])
                    row_dict["pics"] = self._get_local_image_paths(
                        images_data,
                        row_dict["upstream_name"],
                        row_dict["dynamic_id"],
                    )
                except (json.JSONDecodeError, TypeError):
                    row_dict["pics"] = []
            else:
                row_dict["pics"] = []
            
            # 解析视频
            if row_dict.get("video"):
                try:
                    row_dict["video"] = json.loads(row_dict["video"])
                except (json.JSONDecodeError, TypeError):
                    row_dict["video"] = None
            else:
                row_dict["video"] = None
            
            result.append(row_dict)
        
        return result
    
    def _get_local_image_paths(
        self,
        images: list,
        upstream_name: str,
        dynamic_id: str,
    ) -> list[str]:
        """获取本地图片路径"""
        if not images:
            return []
        
        safe_name = "".join(
            c for c in (upstream_name or "") if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_name:
            safe_name = dynamic_id.split("_")[0] if "_" in dynamic_id else dynamic_id
        
        base_dir = Path(self._config.path).parent.parent / "images"
        dynamic_dir = base_dir / safe_name / dynamic_id
        
        result = []
        for i, img in enumerate(images):
            if isinstance(img, dict):
                url = img.get("url", "")
            else:
                url = img
            
            ext = ".jpg"
            if "?" in url:
                base_url = url.split("?")[0]
                if "." in base_url:
                    ext = "." + base_url.rsplit(".", 1)[-1]
            
            filename = f"{i + 1:03d}{ext}"
            local_path = dynamic_dir / filename
            
            if local_path.exists():
                result.append(f"/images/{safe_name}/{dynamic_id}/{filename}")
            else:
                result.append(url)
        
        return result
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        cursor = self._conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM dynamics")
        total_dynamics = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM upstreams")
        total_upstreams = cursor.fetchone()["count"]
        
        cursor.execute(
            """
            SELECT uid, upstream_name, COUNT(*) as count 
            FROM dynamics 
            GROUP BY uid 
            ORDER BY count DESC
            """
        )
        upstream_stats = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_dynamics": total_dynamics,
            "total_upstreams": total_upstreams,
            "upstream_stats": upstream_stats,
        }
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._logger.info("数据库连接已关闭")
    
    def __enter__(self) -> Database:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
