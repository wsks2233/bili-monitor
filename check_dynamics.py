#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看数据库中的动态数据
"""

import sqlite3
import json
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('data/bili_monitor.db')
cursor = conn.cursor()

# 查询动态数据
cursor.execute('''
    SELECT dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, images, stat_like, stat_repost, stat_comment 
    FROM dynamics 
    LIMIT 10
''')

# 打印结果
print("数据库中的动态数据：")
print("-" * 80)

rows = cursor.fetchall()
for row in rows:
    dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, images, stat_like, stat_repost, stat_comment = row
    print(f"动态ID: {dynamic_id}")
    print(f"UP主: {upstream_name}")
    print(f"类型: {dynamic_type}")
    print(f"内容: {content[:100]}..." if content else "内容: 无")
    print(f"发布时间: {publish_time}")
    print(f"图片数量: {len(json.loads(images)) if images else 0}")
    print(f"统计: 点赞={stat_like}, 转发={stat_repost}, 评论={stat_comment}")
    print("-" * 80)

# 关闭连接
conn.close()
