#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试企业微信markdown消息格式
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

def generate_markdown_message(dynamic):
    """生成markdown消息内容"""
    content_lines = []
    
    # 标题
    content_lines.append(f"**{dynamic.upstream_name} 发布了新动态**")
    content_lines.append("")
    
    # 基本信息
    content_lines.append(f"> 类型：`{dynamic.dynamic_type}`")
    content_lines.append(f"> 时间：{dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}")
    content_lines.append("")
    
    # 动态内容
    if dynamic.content:
        content_preview = dynamic.content[:300]
        if len(dynamic.content) > 300:
            content_preview += "..."
        content_lines.append("**内容：**")
        content_lines.append(content_preview)
        content_lines.append("")
    
    # 图片（显示前3张）
    if dynamic.images:
        content_lines.append(f"**图片：**共 {len(dynamic.images)} 张")
        for i, image in enumerate(dynamic.images[:3]):
            content_lines.append(f"![图片{i+1}]({image.url})")
        content_lines.append("")
    
    # 统计信息
    content_lines.append("---")
    content_lines.append(f"👍 {dynamic.stat.like:,}  💬 {dynamic.stat.comment:,}  🔄 {dynamic.stat.repost:,}")
    
    # 链接
    if dynamic.dynamic_type in ['图文', '转发', '充电专属-图文']:
        url = f"https://t.bilibili.com/{dynamic.dynamic_id}"
    else:
        url = f"https://www.bilibili.com/opus/{dynamic.dynamic_id}"
    content_lines.append(f"[查看完整动态]({url})")
    
    return "\n".join(content_lines)

def main():
    """主函数"""
    print("测试企业微信markdown消息格式")
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
    
    # 生成markdown消息
    markdown_content = generate_markdown_message(dynamic)
    
    # 打印生成的markdown消息
    print("\n生成的Markdown消息内容：")
    print("-" * 80)
    print(markdown_content)
    print("-" * 80)
    
    # 打印JSON格式的消息数据
    import json
    message_data = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content
        }
    }
    print("\nJSON格式的消息数据：")
    print("-" * 80)
    print(json.dumps(message_data, ensure_ascii=False, indent=2))
    print("-" * 80)

if __name__ == "__main__":
    main()
