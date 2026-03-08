#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看数据库表结构
"""

import sqlite3

# 连接数据库
conn = sqlite3.connect('data/bili_monitor.db')
cursor = conn.cursor()

# 查看表结构
print("查看dynamics表结构：")
cursor.execute("PRAGMA table_info(dynamics)")
columns = cursor.fetchall()
for column in columns:
    print(f"列名: {column[1]}, 类型: {column[2]}")

print("\n查看upstreams表结构：")
cursor.execute("PRAGMA table_info(upstreams)")
columns = cursor.fetchall()
for column in columns:
    print(f"列名: {column[1]}, 类型: {column[2]}")

# 关闭连接
conn.close()
