#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 到 MySQL 数据迁移工具

使用方法：
    python migrate_to_mysql.py

配置说明：
    1. 确保 config.yaml 中已配置 MySQL 连接信息
    2. 确保 SQLite 数据库文件存在 (data/bili_monitor.db)
    3. 运行此脚本自动迁移数据
"""

import sqlite3
import pymysql
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config


def get_sqlite_connection(sqlite_path: str):
    """获取 SQLite 连接"""
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite 数据库文件不存在：{sqlite_path}")
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    print(f"✅ SQLite 数据库连接成功：{sqlite_path}")
    return conn


def get_mysql_connection(config):
    """获取 MySQL 连接"""
    try:
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        print(f"✅ MySQL 数据库连接成功：{config.host}:{config.port}/{config.database}")
        return conn
    except Exception as e:
        raise ConnectionError(f"MySQL 连接失败：{e}")


def migrate_table(sqlite_conn, mysql_conn, table_name: str, primary_key: str, ignore_fields: list = None):
    """迁移单个表"""
    if ignore_fields is None:
        ignore_fields = ['id', 'updated_at']
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    # 获取 SQLite 表的所有数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"⚠️  表 {table_name} 为空，跳过迁移")
        return 0
    
    # 获取字段名
    columns = [description[0] for description in sqlite_cursor.description]
    insert_columns = [col for col in columns if col not in ignore_fields]
    
    print(f"📦 开始迁移表 {table_name}，共 {len(rows)} 条记录")
    
    migrated_count = 0
    for row in rows:
        try:
            # 准备数据
            data = {}
            for col in columns:
                value = row[col]
                # 处理 datetime 类型
                if isinstance(value, str) and col in ['publish_time', 'create_time']:
                    try:
                        value = datetime.fromisoformat(value)
                    except:
                        pass
                data[col] = value
            
            # 构建 INSERT ... ON DUPLICATE KEY UPDATE 语句
            columns_str = ', '.join([f"`{col}`" for col in insert_columns])
            placeholders = ', '.join(['%s' for _ in insert_columns])
            update_clause = ', '.join([f"`{col}` = VALUES(`{col}`)" for col in insert_columns if col != primary_key])
            
            sql = f"""
                INSERT INTO {table_name} ({columns_str})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {update_clause}
            """
            
            values = [data[col] for col in insert_columns]
            mysql_cursor.execute(sql, values)
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ 迁移 {table_name} 记录失败：{e}")
            continue
    
    mysql_conn.commit()
    print(f"✅ 表 {table_name} 迁移完成，成功 {migrated_count}/{len(rows)} 条")
    return migrated_count


def verify_migration(sqlite_conn, mysql_conn):
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("验证迁移结果")
    print("=" * 60)
    
    tables = ['dynamics', 'upstreams']
    
    for table in tables:
        sqlite_cursor = sqlite_conn.cursor()
        mysql_cursor = mysql_conn.cursor()
        
        sqlite_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()['count']
        
        mysql_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        mysql_count = mysql_cursor.fetchone()['count']
        
        status = "✅" if sqlite_count == mysql_count else "❌"
        print(f"{status} 表 {table}: SQLite={sqlite_count}, MySQL={mysql_count}")


def main():
    print("=" * 60)
    print("SQLite 到 MySQL 数据迁移工具")
    print("=" * 60)
    print()
    
    # 加载配置
    try:
        config = load_config('config.yaml')
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        print("请确保 config.yaml 存在并配置正确")
        return 1
    
    # 检查数据库配置
    if config.database.type.lower() != 'mysql':
        print("❌ 配置文件中的数据库类型不是 MySQL")
        print("请先修改 config.yaml 中的 database.type 为 mysql")
        return 1
    
    # 连接 SQLite
    try:
        sqlite_path = config.database.path if hasattr(config.database, 'path') else 'data/bili_monitor.db'
        # 如果是 MySQL 配置，SQLite 路径使用默认值
        if not os.path.exists(sqlite_path):
            sqlite_path = 'data/bili_monitor.db'
        
        sqlite_conn = get_sqlite_connection(sqlite_path)
    except Exception as e:
        print(f"❌ SQLite 连接失败：{e}")
        return 1
    
    # 连接 MySQL
    try:
        mysql_conn = get_mysql_connection(config.database)
    except Exception as e:
        print(f"❌ MySQL 连接失败：{e}")
        sqlite_conn.close()
        return 1
    
    try:
        # 迁移数据
        print("\n" + "=" * 60)
        print("开始迁移数据")
        print("=" * 60)
        
        # 迁移 dynamics 表
        migrate_table(
            sqlite_conn, mysql_conn, 
            'dynamics', 
            primary_key='dynamic_id',
            ignore_fields=['id', 'updated_at']
        )
        
        # 迁移 upstreams 表
        migrate_table(
            sqlite_conn, mysql_conn,
            'upstreams',
            primary_key='uid',
            ignore_fields=['id', 'updated_at']
        )
        
        # 验证迁移结果
        verify_migration(sqlite_conn, mysql_conn)
        
        print("\n" + "=" * 60)
        print("✅ 数据迁移完成！")
        print("=" * 60)
        print("\n下一步操作：")
        print("1. 验证数据是否正确迁移")
        print("2. 修改 config.yaml 中的 database.type 为 mysql")
        print("3. 重启监控程序")
        print("4. (可选) 备份旧的 SQLite 数据库文件")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        sqlite_conn.close()
        mysql_conn.close()
        print("\n数据库连接已关闭")


if __name__ == '__main__':
    sys.exit(main())
