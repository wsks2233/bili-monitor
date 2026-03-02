#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态查看工具 - 查看保存的动态数据和图片
"""

import sqlite3
import json
import os
import webbrowser
from datetime import datetime

DB_PATH = 'data/bili_monitor.db'
IMAGES_DIR = 'images'


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_upstreams():
    """列出所有监控的UP主"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM upstreams')
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "=" * 60)
    print("已监控的UP主列表")
    print("=" * 60)
    
    for row in rows:
        print(f"UID: {row['uid']}")
        print(f"名称: {row['name']}")
        print(f"粉丝: {row['fans']:,}")
        print(f"签名: {row['sign'][:50] if row['sign'] else '无'}...")
        print("-" * 40)
    
    return [row['uid'] for row in rows]


def list_dynamics(uid=None, limit=20, with_images_only=False):
    """列出动态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if uid:
        cursor.execute('''
            SELECT * FROM dynamics 
            WHERE uid = ? 
            ORDER BY publish_time DESC 
            LIMIT ?
        ''', (uid, limit))
    else:
        cursor.execute('''
            SELECT * FROM dynamics 
            ORDER BY publish_time DESC 
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"动态列表 (共 {len(rows)} 条)")
    print("=" * 80)
    
    for i, row in enumerate(rows, 1):
        images = json.loads(row['images']) if row['images'] else []
        
        if with_images_only and not images:
            continue
        
        print(f"\n[{i}] 动态ID: {row['dynamic_id']}")
        print(f"    类型: {row['dynamic_type']}")
        print(f"    UP主: {row['upstream_name']}")
        
        content = (row['content'][:100] if row['content'] else "无内容").replace('\u200b', '')
        print(f"    内容: {content}...")
        
        if row['video']:
            video = json.loads(row['video'])
            print(f"    视频: {video.get('title', '无标题')}")
            print(f"    BVID: {video.get('bvid', '无')}")
        
        if images:
            print(f"    图片: {len(images)} 张")
            for j, img in enumerate(images[:3], 1):
                print(f"      [{j}] {img['url'][:60]}...")
        
        pub_time = row['publish_time']
        print(f"    发布时间: {pub_time}")
        print(f"    互动: 点赞 {row['stat_like']:,}, 评论 {row['stat_comment']:,}")
    
    return rows


def show_dynamic_detail(dynamic_id):
    """显示动态详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dynamics WHERE dynamic_id = ?', (dynamic_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"未找到动态: {dynamic_id}")
        return
    
    print("\n" + "=" * 80)
    print(f"动态详情: {dynamic_id}")
    print("=" * 80)
    
    print(f"UP主: {row['upstream_name']} (UID: {row['uid']})")
    print(f"类型: {row['dynamic_type']}")
    print(f"发布时间: {row['publish_time']}")
    print(f"更新时间: {row['updated_at']}")
    
    print(f"\n内容:\n{row['content'] or '无内容'}")
    
    if row['video']:
        video = json.loads(row['video'])
        print(f"\n视频信息:")
        print(f"  标题: {video.get('title', '无')}")
        print(f"  BVID: {video.get('bvid', '无')}")
        print(f"  AID: {video.get('aid', '无')}")
        print(f"  封面: {video.get('cover', '无')}")
    
    images = json.loads(row['images']) if row['images'] else []
    if images:
        print(f"\n图片 ({len(images)} 张):")
        for i, img in enumerate(images, 1):
            print(f"  [{i}] {img['url']}")
            print(f"      尺寸: {img['width']} x {img['height']}")
    
    print(f"\n互动数据:")
    print(f"  点赞: {row['stat_like']:,}")
    print(f"  转发: {row['stat_repost']:,}")
    print(f"  评论: {row['stat_comment']:,}")


def open_dynamic_in_browser(dynamic_id):
    """在浏览器中打开动态"""
    if dynamic_id.startswith('av'):
        url = f"https://www.bilibili.com/video/{dynamic_id}"
    else:
        url = f"https://www.bilibili.com/opus/{dynamic_id}"
    
    print(f"正在打开: {url}")
    webbrowser.open(url)


def open_image_in_browser(image_url):
    """在浏览器中打开图片"""
    print(f"正在打开图片: {image_url}")
    webbrowser.open(image_url)


def export_to_json(output_file='dynamics_export.json'):
    """导出动态到JSON文件"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dynamics ORDER BY publish_time DESC')
    rows = cursor.fetchall()
    conn.close()
    
    dynamics = []
    for row in rows:
        dynamics.append({
            'dynamic_id': row['dynamic_id'],
            'uid': row['uid'],
            'upstream_name': row['upstream_name'],
            'dynamic_type': row['dynamic_type'],
            'content': row['content'],
            'publish_time': row['publish_time'],
            'video': json.loads(row['video']) if row['video'] else None,
            'images': json.loads(row['images']) if row['images'] else [],
            'stat': {
                'like': row['stat_like'],
                'repost': row['stat_repost'],
                'comment': row['stat_comment'],
            }
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dynamics, f, ensure_ascii=False, indent=2)
    
    print(f"已导出 {len(dynamics)} 条动态到: {output_file}")


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 50)
        print("B站动态查看工具")
        print("=" * 50)
        print("1. 查看UP主列表")
        print("2. 查看动态列表")
        print("3. 查看动态详情")
        print("4. 在浏览器中打开动态")
        print("5. 查看有图片的动态")
        print("6. 导出动态到JSON")
        print("0. 退出")
        print("-" * 50)
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            list_upstreams()
        
        elif choice == '2':
            uid = input("输入UP主UID (留空查看全部): ").strip()
            limit = input("显示数量 (默认20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            list_dynamics(uid if uid else None, limit)
        
        elif choice == '3':
            dynamic_id = input("输入动态ID: ").strip()
            show_dynamic_detail(dynamic_id)
        
        elif choice == '4':
            dynamic_id = input("输入动态ID: ").strip()
            open_dynamic_in_browser(dynamic_id)
        
        elif choice == '5':
            list_dynamics(with_images_only=True)
        
        elif choice == '6':
            filename = input("输出文件名 (默认dynamics_export.json): ").strip()
            export_to_json(filename if filename else 'dynamics_export.json')
        
        elif choice == '0':
            print("再见!")
            break
        
        else:
            print("无效选择，请重试")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'upstreams':
            list_upstreams()
        elif command == 'list':
            uid = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            list_dynamics(uid, limit)
        elif command == 'detail':
            if len(sys.argv) > 2:
                show_dynamic_detail(sys.argv[2])
        elif command == 'open':
            if len(sys.argv) > 2:
                open_dynamic_in_browser(sys.argv[2])
        elif command == 'export':
            filename = sys.argv[2] if len(sys.argv) > 2 else 'dynamics_export.json'
            export_to_json(filename)
        else:
            print(f"未知命令: {command}")
            print("可用命令: upstreams, list, detail, open, export")
    else:
        interactive_menu()
