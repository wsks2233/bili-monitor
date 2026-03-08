#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查动态链接格式
"""

import sqlite3
import json
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('data/bili_monitor.db')
cursor = conn.cursor()

# 查询带有图片的动态
cursor.execute('''
    SELECT dynamic_id, upstream_name, dynamic_type, content, publish_time, images 
    FROM dynamics 
    WHERE images IS NOT NULL AND images != '[]' 
    LIMIT 5
''')

# 打印结果
print("动态链接检查：")
print("-" * 80)

rows = cursor.fetchall()
for row in rows:
    dynamic_id, upstream_name, dynamic_type, content, publish_time, images = row
    print(f"动态ID: {dynamic_id}")
    print(f"UP主: {upstream_name}")
    print(f"类型: {dynamic_type}")
    print(f"生成的链接: https://www.bilibili.com/opus/{dynamic_id}")
    print("-" * 80)

# 关闭连接
conn.close()
