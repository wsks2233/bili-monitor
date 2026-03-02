# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import json
from typing import List, Optional, Set
from datetime import datetime
from abc import ABC, abstractmethod

from ..core.models import DynamicInfo, UpstreamInfo
from ..core.config import DatabaseConfig


class DatabaseError(Exception):
    pass


class DatabaseBase(ABC):
    @abstractmethod
    def init_db(self) -> None:
        pass
    
    @abstractmethod
    def save_dynamic(self, dynamic: DynamicInfo) -> bool:
        pass
    
    @abstractmethod
    def dynamic_exists(self, dynamic_id: str) -> bool:
        pass
    
    @abstractmethod
    def get_processed_ids(self, uid: str, limit: int = 100) -> Set[str]:
        pass
    
    @abstractmethod
    def save_upstream(self, upstream: UpstreamInfo) -> bool:
        pass
    
    @abstractmethod
    def get_upstream(self, uid: str) -> Optional[UpstreamInfo]:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass


class SQLiteDatabase(DatabaseBase):
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
        cursor = self.conn.cursor()
        if uid:
            cursor.execute('''
                SELECT * FROM dynamics 
                WHERE uid = ? 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
            ''', (uid, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM dynamics 
                ORDER BY publish_time DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
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


class MySQLDatabase(DatabaseBase):
    def __init__(self, config: DatabaseConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger('bili-monitor')
        self.conn = None
        self._init_connection()
    
    def _init_connection(self) -> None:
        try:
            import pymysql
            self.conn = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
            )
            self.logger.info(f"MySQL数据库连接成功: {self.config.host}:{self.config.port}")
            self.init_db()
        except ImportError:
            raise DatabaseError("请安装pymysql: pip install pymysql")
        except Exception as e:
            raise DatabaseError(f"MySQL连接失败: {e}")
    
    def init_db(self) -> None:
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dynamics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dynamic_id VARCHAR(64) UNIQUE NOT NULL,
                uid VARCHAR(32) NOT NULL,
                upstream_name VARCHAR(128),
                dynamic_type VARCHAR(64),
                content TEXT,
                publish_time DATETIME,
                create_time DATETIME,
                images JSON,
                video JSON,
                stat_like INT DEFAULT 0,
                stat_repost INT DEFAULT 0,
                stat_comment INT DEFAULT 0,
                raw_json JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_uid (uid),
                INDEX idx_publish_time (publish_time),
                INDEX idx_dynamic_id (dynamic_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upstreams (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(32) UNIQUE NOT NULL,
                name VARCHAR(128),
                face VARCHAR(512),
                sign TEXT,
                level INT DEFAULT 0,
                fans INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        self.conn.commit()
        self.logger.info("MySQL数据库表初始化完成")
    
    def save_dynamic(self, dynamic: DynamicInfo) -> bool:
        try:
            cursor = self.conn.cursor()
            
            images_json = json.dumps([img.to_dict() for img in dynamic.images], ensure_ascii=False)
            video_json = json.dumps(dynamic.video.to_dict(), ensure_ascii=False) if dynamic.video else None
            raw_json = json.dumps(dynamic.raw_json, ensure_ascii=False) if dynamic.raw_json else None
            
            cursor.execute('''
                INSERT INTO dynamics 
                (dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, 
                 create_time, images, video, stat_like, stat_repost, stat_comment, raw_json, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                upstream_name = VALUES(upstream_name),
                dynamic_type = VALUES(dynamic_type),
                content = VALUES(content),
                images = VALUES(images),
                video = VALUES(video),
                stat_like = VALUES(stat_like),
                stat_repost = VALUES(stat_repost),
                stat_comment = VALUES(stat_comment),
                raw_json = VALUES(raw_json),
                updated_at = NOW()
            ''', (
                dynamic.dynamic_id,
                dynamic.uid,
                dynamic.upstream_name,
                dynamic.dynamic_type,
                dynamic.content,
                dynamic.publish_time,
                dynamic.create_time,
                images_json,
                video_json,
                dynamic.stat.like,
                dynamic.stat.repost,
                dynamic.stat.comment,
                raw_json,
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
        cursor.execute('SELECT 1 FROM dynamics WHERE dynamic_id = %s', (dynamic_id,))
        return cursor.fetchone() is not None
    
    def get_processed_ids(self, uid: str, limit: int = 100) -> Set[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT dynamic_id FROM dynamics 
            WHERE uid = %s 
            ORDER BY publish_time DESC 
            LIMIT %s
        ''', (uid, limit))
        return {row['dynamic_id'] for row in cursor.fetchall()}
    
    def save_upstream(self, upstream: UpstreamInfo) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO upstreams (uid, name, face, sign, level, fans, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                face = VALUES(face),
                sign = VALUES(sign),
                level = VALUES(level),
                fans = VALUES(fans),
                updated_at = NOW()
            ''', (
                upstream.uid,
                upstream.name,
                upstream.face,
                upstream.sign,
                upstream.level,
                upstream.fans,
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
        cursor.execute('SELECT * FROM upstreams WHERE uid = %s', (uid,))
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
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.logger.info("MySQL数据库连接已关闭")


def create_database(config: DatabaseConfig, logger: Optional[logging.Logger] = None) -> DatabaseBase:
    db_type = config.type.lower()
    
    if db_type == 'sqlite':
        return SQLiteDatabase(config, logger)
    elif db_type == 'mysql':
        return MySQLDatabase(config, logger)
    else:
        raise DatabaseError(f"不支持的数据库类型: {db_type}")


Database = SQLiteDatabase
