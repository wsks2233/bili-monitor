#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库初始化脚本

使用方法：
    python init_mysql.py

功能：
    1. 创建数据库（如果不存在）
    2. 创建表结构
    3. 验证连接
"""

import pymysql
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config


def create_database_if_not_exists(config) -> bool:
    """创建数据库（如果不存在）"""
    try:
        # 先连接到 MySQL 服务器（不指定数据库）
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            charset='utf8mb4',
        )
        
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{config.database}'")
        if not cursor.fetchone():
            # 创建数据库
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{config.database}`
                DEFAULT CHARACTER SET utf8mb4
                DEFAULT COLLATE utf8mb4_unicode_ci
            """)
            print(f"✅ 数据库 {config.database} 创建成功")
        else:
            print(f"ℹ️  数据库 {config.database} 已存在")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建数据库失败：{e}")
        return False


def init_database_tables(config):
    """初始化数据库表"""
    try:
        # 连接到指定数据库
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        
        cursor = conn.cursor()
        
        print(f"✅ MySQL 数据库连接成功：{config.host}:{config.port}/{config.database}")
        
        # 创建 dynamics 表
        cursor.execute("""
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
        """)
        print("✅ 表 dynamics 创建成功")
        
        # 创建 upstreams 表
        cursor.execute("""
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
        """)
        print("✅ 表 upstreams 创建成功")
        
        # 创建 state 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state (
                id INT AUTO_INCREMENT PRIMARY KEY,
                key VARCHAR(128) UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 表 state 创建成功")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ MySQL 数据库初始化完成！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化数据库表失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("MySQL 数据库初始化工具")
    print("=" * 60)
    print()
    
    # 加载配置
    try:
        config = load_config('config.yaml')
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        return 1
    
    # 检查数据库配置
    if config.database.type.lower() != 'mysql':
        print("⚠️  配置文件中的数据库类型不是 MySQL")
        print("将使用配置文件中的 MySQL 连接信息进行初始化")
        print()
    
    # 创建数据库
    if not create_database_if_not_exists(config.database):
        print("\n❌ 数据库创建失败，请检查 MySQL 连接配置")
        return 1
    
    # 初始化表
    if not init_database_tables(config.database):
        return 1
    
    print("\n下一步操作：")
    print("1. 确认 config.yaml 中 database.type = mysql")
    print("2. 运行 python main.py 启动监控程序")
    print("3. (可选) 运行 python migrate_to_mysql.py 迁移旧数据")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
