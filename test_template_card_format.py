#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试企业微信模板卡片消息格式
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from bili_monitor.core.models import DynamicInfo, ImageInfo, StatInfo

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 连接数据库
def get_dynamic_with_images():
    """从数据库中获取一条带有图片的动态"""
    conn = sqlite3.connect('data/bili_monitor.db')
    cursor = conn.cursor()
    
    # 查询带有图片的动态
    cursor.execute('''
        SELECT dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, images, stat_like, stat_repost, stat_comment 
        FROM dynamics 
        WHERE images IS NOT NULL AND images != '[]' 
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    if not row:
        print("❌ 数据库中没有带有图片的动态")
        return None
    
    dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, images_json, stat_like, stat_repost, stat_comment = row
    
    # 解析图片数据
    images = []
    if images_json:
        try:
            images_data = json.loads(images_json)
            for img_data in images_data:
                images.append(ImageInfo(
                    url=img_data.get('url', ''),
                    width=img_data.get('width', 0),
                    height=img_data.get('height', 0)
                ))
        except Exception as e:
            print(f"❌ 解析图片数据失败: {e}")
    
    # 创建动态对象
    dynamic = DynamicInfo(
        dynamic_id=dynamic_id,
        uid=uid,
        upstream_name=upstream_name,
        dynamic_type=dynamic_type,
        content=content,
        publish_time=datetime.fromisoformat(publish_time),
        images=images,
        stat=StatInfo(
            like=stat_like,
            repost=stat_repost,
            comment=stat_comment
        )
    )
    
    conn.close()
    return dynamic

def generate_template_card_message(dynamic):
    """生成模板卡片消息"""
    # 根据动态类型生成正确的链接
    if dynamic.dynamic_type in ['图文', '转发', '充电专属-图文']:
        url = f"https://t.bilibili.com/{dynamic.dynamic_id}"
    else:
        url = f"https://www.bilibili.com/opus/{dynamic.dynamic_id}"
    
    # 构建模板卡片消息
    template_card = {
        "card_type": "news_notice",
        "source": {
            "icon_url": "https://i0.hdslb.com/bfs/face/member/noface.jpg",
            "desc": "B站动态监控",
            "desc_color": 0
        },
        "main_title": {
            "title": f"{dynamic.upstream_name} 发布了新动态",
            "desc": f"类型: {dynamic.dynamic_type} | 时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}"
        },
        "card_action": {
            "type": 1,
            "url": url
        }
    }
    
    # 添加图片（如果有）
    if dynamic.images:
        template_card["card_image"] = {
            "url": dynamic.images[0].url,
            "aspect_ratio": 1.3
        }
    
    # 添加内容预览（如果有）
    if dynamic.content:
        content_preview = dynamic.content[:100]
        if len(dynamic.content) > 100:
            content_preview += "..."
        template_card["vertical_content_list"] = [
            {
                "title": "内容预览",
                "desc": content_preview
            }
        ]
    
    # 添加统计信息
    template_card["horizontal_content_list"] = [
        {
            "keyname": "点赞",
            "value": f"{dynamic.stat.like:,}"
        },
        {
            "keyname": "评论",
            "value": f"{dynamic.stat.comment:,}"
        },
        {
            "keyname": "转发",
            "value": f"{dynamic.stat.repost:,}"
        }
    ]
    
    # 添加跳转按钮
    template_card["jump_list"] = [
        {
            "type": 1,
            "title": "查看完整动态",
            "url": url
        }
    ]
    
    # 构建消息数据
    message_data = {
        "msgtype": "template_card",
        "template_card": template_card
    }
    
    return message_data

def main():
    """主函数"""
    print("测试企业微信模板卡片消息格式")
    print("=" * 80)
    
    # 获取带有图片的动态
    dynamic = get_dynamic_with_images()
    if not dynamic:
        return
    
    # 打印动态信息
    print(f"动态ID: {dynamic.dynamic_id}")
    print(f"UP主: {dynamic.upstream_name}")
    print(f"类型: {dynamic.dynamic_type}")
    print(f"图片数量: {len(dynamic.images)}")
    print("=" * 80)
    
    # 生成模板卡片消息
    message_data = generate_template_card_message(dynamic)
    
    # 打印生成的模板卡片消息
    print("\n生成的模板卡片消息：")
    print("-" * 80)
    print(json.dumps(message_data, ensure_ascii=False, indent=2))
    print("-" * 80)

if __name__ == "__main__":
    main()
