# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import json
from typing import List, Optional, Set
from datetime import datetime

from ..core.models import DynamicInfo, UpstreamInfo
from ..core.config import DatabaseConfig


class DatabaseError(Exception):
    pass


class Database:
    def __init__(self, config: DatabaseConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger('bili-monitor')
        self.conn: Optional[sqlite3.Connection] = None
        self._init_connection()
    
    def _init_connection(self) -> None:
        db_dir = os.path.dirname(self.config.path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(self.config.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.logger.info(f"SQLite数据库连接成功: {self.config.path}")
        self.init_db()
    
    def init_db(self) -> None:
        cursor = self.conn.cursor()
        
        cursor.execute('''
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
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dynamics_uid ON dynamics(uid)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dynamics_publish_time ON dynamics(publish_time)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dynamics_dynamic_id ON dynamics(dynamic_id)
        ''')
        # 复合索引优化常见查询模式
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dynamics_uid_publish ON dynamics(uid, publish_time DESC)
        ''')
        
        cursor.execute('''
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
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        self.logger.info("数据库表初始化完成")
    
    def save_dynamic(self, dynamic: DynamicInfo) -> bool:
        try:
            cursor = self.conn.cursor()
            
            images_json = json.dumps([img.to_dict() for img in dynamic.images], ensure_ascii=False)
            video_json = json.dumps(dynamic.video.to_dict(), ensure_ascii=False) if dynamic.video else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO dynamics 
                (dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, 
                 create_time, images, video, stat_like, stat_repost, stat_comment, raw_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
                json.dumps(dynamic.raw_json, ensure_ascii=False) if dynamic.raw_json else None,
                datetime.now().isoformat(),
            ))
            
            self.conn.commit()
            self.logger.debug(f"保存动态成功: {dynamic.dynamic_id}")
            return True
        except Exception as e:
            self.logger.error(f"保存动态失败: {e}")
            self.conn.rollback()
            return False
    
    def dynamic_exists(self, dynamic_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM dynamics WHERE dynamic_id = ?', (dynamic_id,))
        return cursor.fetchone() is not None
    
    def get_processed_ids(self, uid: str, limit: int = 100) -> Set[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT dynamic_id FROM dynamics 
            WHERE uid = ? 
            ORDER BY publish_time DESC 
            LIMIT ?
        ''', (uid, limit))
        return {row['dynamic_id'] for row in cursor.fetchall()}
    
    def save_upstream(self, upstream: UpstreamInfo) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO upstreams (uid, name, face, sign, level, fans, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                upstream.uid,
                upstream.name,
                upstream.face,
                upstream.sign,
                upstream.level,
                upstream.fans,
                datetime.now().isoformat(),
            ))
            self.conn.commit()
            self.logger.debug(f"保存UP主信息成功: {upstream.uid}")
            return True
        except Exception as e:
            self.logger.error(f"保存UP主信息失败: {e}")
            self.conn.rollback()
            return False
    
    def get_upstream(self, uid: str) -> Optional[UpstreamInfo]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM upstreams WHERE uid = ?', (uid,))
        row = cursor.fetchone()
        if row:
            return UpstreamInfo(
                uid=row['uid'],
                name=row['name'],
                face=row['face'],
                sign=row['sign'],
                level=row['level'],
                fans=row['fans'],
            )
        return None
    
    def get_dynamics(self, uid: str = None, limit: int = 50, offset: int = 0) -> List[dict]:
        """获取动态列表，优化查询性能"""
        cursor = self.conn.cursor()
        
        if uid:
            cursor.execute('''
                SELECT dynamic_id, uid, upstream_name, dynamic_type, content, 
                       publish_time, create_time, images, video, 
                       stat_like, stat_repost, stat_comment
                FROM dynamics 
                WHERE uid = ? 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
            ''', (uid, limit, offset))
        else:
            cursor.execute('''
                SELECT dynamic_id, uid, upstream_name, dynamic_type, content, 
                       publish_time, create_time, images, video, 
                       stat_like, stat_repost, stat_comment
                FROM dynamics 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            row_dict = dict(row)
            row_dict['like_count'] = row_dict.pop('stat_like', 0)
            row_dict['repost_count'] = row_dict.pop('stat_repost', 0)
            row_dict['comment_count'] = row_dict.pop('stat_comment', 0)
            
            if row_dict.get('images'):
                try:
                    images_data = json.loads(row_dict['images'])
                    row_dict['pics'] = self._get_local_image_paths(
                        images_data, 
                        row_dict['upstream_name'], 
                        row_dict['dynamic_id']
                    )
                except (json.JSONDecodeError, TypeError):
                    row_dict['pics'] = []
            else:
                row_dict['pics'] = []
            
            if row_dict.get('video'):
                try:
                    row_dict['video'] = json.loads(row_dict['video'])
                except (json.JSONDecodeError, TypeError):
                    row_dict['video'] = None
            else:
                row_dict['video'] = None
            result.append(row_dict)
        
        return result
    
    def _get_local_image_paths(self, images: list, upstream_name: str, dynamic_id: str) -> list:
        """获取本地图片路径，如果存在则返回本地路径，否则返回原始URL"""
        if not images:
            return []
        
        import os
        
        safe_name = "".join(c for c in (upstream_name or '') if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = dynamic_id.split('_')[0] if '_' in dynamic_id else dynamic_id
        
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "images")
        dynamic_dir = os.path.join(base_dir, safe_name, dynamic_id)
        
        result = []
        for i, img in enumerate(images):
            if isinstance(img, dict):
                url = img.get('url', '')
            else:
                url = img
            
            ext = '.jpg'
            if '?' in url:
                base_url = url.split('?')[0]
                if '.' in base_url:
                    ext = '.' + base_url.rsplit('.', 1)[-1]
            
            filename = f"{i+1:03d}{ext}"
            local_path = os.path.join(dynamic_dir, filename)
            
            if os.path.exists(local_path):
                result.append(f"/images/{safe_name}/{dynamic_id}/{filename}")
            else:
                result.append(url)
        
        return result
    
    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM dynamics')
        total_dynamics = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM upstreams')
        total_upstreams = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT uid, upstream_name, COUNT(*) as count 
            FROM dynamics 
            GROUP BY uid 
            ORDER BY count DESC
        ''')
        upstream_stats = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_dynamics': total_dynamics,
            'total_upstreams': total_upstreams,
            'upstream_stats': upstream_stats,
        }
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.logger.info("数据库连接已关闭")
