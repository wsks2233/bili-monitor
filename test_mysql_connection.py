#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 连接测试工具

使用方法：
    python test_mysql_connection.py

功能：
    1. 测试 MySQL 连接
    2. 显示数据库信息
    3. 验证权限
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config


def test_mysql_connection():
    """测试 MySQL 连接"""
    print("=" * 60)
    print("MySQL 连接测试")
    print("=" * 60)
    print()
    
    # 加载配置
    try:
        config = load_config('config.yaml')
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        return False
    
    # 检查数据库类型
    if config.database.type.lower() != 'mysql':
        print(f"⚠️  当前数据库类型：{config.database.type}")
        print("提示：MySQL 配置示例:")
        print("""
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: bili_monitor
        """)
        return False
    
    print(f"\n📋 连接信息:")
    print(f"  主机：{config.database.host}:{config.database.port}")
    print(f"  用户：{config.database.user}")
    print(f"  数据库：{config.database.database}")
    print()
    
    # 尝试连接
    try:
        import pymysql
        
        print("🔌 正在连接 MySQL...")
        conn = pymysql.connect(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database,
            charset='utf8mb4',
            connect_timeout=10,
        )
        
        print("✅ MySQL 连接成功！")
        
        # 获取数据库信息
        cursor = conn.cursor()
        
        # MySQL 版本
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"\n📊 数据库信息:")
        print(f"  MySQL 版本：{version[0]}")
        
        # 数据库字符集
        cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
        charset = cursor.fetchone()
        print(f"  字符集：{charset[1]}")
        
        # 数据库排序规则
        cursor.execute("SHOW VARIABLES LIKE 'collation_database'")
        collation = cursor.fetchone()
        print(f"  排序规则：{collation[1]}")
        
        # 检查表是否存在
        cursor.execute(f"SHOW TABLES FROM `{config.database.database}`")
        tables = cursor.fetchall()
        print(f"\n📁 现有表:")
        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  (空数据库，需要运行 init_mysql.py 初始化)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ MySQL 连接测试通过！")
        print("=" * 60)
        print("\n下一步操作：")
        print("1. 如果是新数据库，运行：python init_mysql.py")
        print("2. 如果从 SQLite 迁移，运行：python migrate_to_mysql.py")
        print("3. 启动监控程序：python main.py")
        
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n❌ 连接失败：{e}")
        print("\n可能的原因：")
        print("  1. MySQL 服务未启动")
        print("  2. 主机名或端口错误")
        print("  3. 用户名或密码错误")
        print("  4. 数据库不存在")
        print("  5. 防火墙阻止连接")
        return False
        
    except pymysql.err.AccessDeniedError as e:
        print(f"\n❌ 访问被拒绝：{e}")
        print("\n请检查：")
        print("  1. 用户名和密码是否正确")
        print("  2. 用户是否有数据库访问权限")
        print("  3. 用户是否允许从该主机连接")
        return False
        
    except ImportError:
        print("\n❌ 缺少 pymysql 库")
        print("请安装：pip install pymysql")
        return False
        
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
