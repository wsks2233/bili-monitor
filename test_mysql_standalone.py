#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 连接测试工具（独立版）

使用方法：
    python test_mysql_standalone.py

功能：
    1. 测试 MySQL 连接（不依赖项目其他模块）
    2. 显示数据库信息
    3. 验证权限
"""

import sys
import os

try:
    import pymysql
    print("✅ pymysql 已安装")
except ImportError:
    print("❌ 缺少 pymysql 库")
    print("请安装：pip install pymysql")
    sys.exit(1)

try:
    import yaml
    print("✅ pyyaml 已安装")
except ImportError:
    print("❌ 缺少 pyyaml 库")
    print("请安装：pip install pyyaml")
    sys.exit(1)


def load_config_simple(config_path='config.yaml'):
    """简单加载配置"""
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在：{config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def test_mysql_connection():
    """测试 MySQL 连接"""
    print("=" * 60)
    print("MySQL 连接测试（独立版）")
    print("=" * 60)
    print()
    
    # 加载配置
    config = load_config_simple()
    if not config:
        print("\n提示：请先创建 config.yaml 文件")
        print("可以复制 config.example.yaml 为 config.yaml")
        return False
    
    db_config = config.get('database', {})
    
    # 检查数据库类型
    db_type = db_config.get('type', 'sqlite').lower()
    if db_type != 'mysql':
        print(f"⚠️  当前数据库类型：{db_type}")
        print("\n要使用 MySQL，请修改 config.yaml：")
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
    
    # 获取 MySQL 配置
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 3306)
    user = db_config.get('user', 'root')
    password = db_config.get('password', '')
    database = db_config.get('database', 'bili_monitor')
    
    print(f"📋 连接信息:")
    print(f"  主机：{host}:{port}")
    print(f"  用户：{user}")
    print(f"  数据库：{database}")
    print()
    
    # 尝试连接
    try:
        print("🔌 正在连接 MySQL...")
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
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
        if charset:
            print(f"  字符集：{charset[1]}")
        
        # 数据库排序规则
        cursor.execute("SHOW VARIABLES LIKE 'collation_database'")
        collation = cursor.fetchone()
        if collation:
            print(f"  排序规则：{collation[1]}")
        
        # 检查表是否存在
        cursor.execute(f"SHOW TABLES FROM `{database}`")
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
        print("\n解决方案：")
        print("  - Windows: net start MySQL80")
        print("  - Linux: sudo systemctl start mysql")
        print("  - 检查 config.yaml 中的配置")
        return False
        
    except pymysql.err.AccessDeniedError as e:
        print(f"\n❌ 访问被拒绝：{e}")
        print("\n请检查：")
        print("  1. 用户名和密码是否正确")
        print("  2. 用户是否有数据库访问权限")
        print("  3. 用户是否允许从该主机连接")
        return False
        
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
