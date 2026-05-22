# -*- coding: utf-8 -*-
"""
存储模块

包含：
- database: 数据库操作（SQLite）
"""

from .database import Database, DatabaseError

__all__ = [
    'Database',
    'DatabaseError',
]
