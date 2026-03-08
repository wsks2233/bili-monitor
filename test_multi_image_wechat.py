#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多图片动态消息推送给企业微信
"""

import sys
import os
import logging
import sqlite3
import json
from datetime import datetime
from bili_monitor.core.models import DynamicInfo, ImageInfo, StatInfo
from bili_monitor.notification.wechat import WeChatNotifier

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_dynamic_with_multiple_images():
    """从数据库中获取一条带有多张图片的动态"""
    logger.info("从数据库中获取带有多张图片的动态...")
    conn = sqlite3.connect('data/bili_monitor.db')
    cursor = conn.cursor()
    
    # 查询带有多张图片的动态
    cursor.execute('''
        SELECT dynamic_id, uid, upstream_name, dynamic_type, content, publish_time, images, stat_like, stat_repost, stat_comment 
        FROM dynamics 
        WHERE images IS NOT NULL AND images != '[]' 
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    if not row:
        logger.error("数据库中没有带有图片的动态")
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
            logger.info(f"成功解析 {len(images)} 张图片")
        except Exception as e:
            logger.error(f"解析图片数据失败: {e}")
    
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

def test_wechat_notification(dynamic):
    """测试企业微信通知"""
    logger.info("测试企业微信通知...")
    
    # 企业微信机器人配置
    wechat_config = {
        "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fa563bd2-035c-448c-b87a-1c9c02832a5a"
    }
    
    # 创建微信通知器
    wechat_notifier = WeChatNotifier(**wechat_config)
    
    # 发送通知
    try:
        result = wechat_notifier.send(dynamic)
        if result.success:
            logger.info(f"企业微信通知发送成功：{result.message}")
            print(f"✅ 企业微信通知发送成功：{result.message}")
        else:
            logger.error(f"企业微信通知发送失败：{result.message}")
            print(f"❌ 企业微信通知发送失败：{result.message}")
    except Exception as e:
        logger.error(f"企业微信通知发送异常：{e}", exc_info=True)
        print(f"❌ 企业微信通知发送异常：{e}")

def main():
    """主函数"""
    logger.info("开始测试多图片动态消息推送给企业微信")
    print("测试多图片动态消息推送给企业微信")
    print("=" * 80)
    
    # 获取带有多张图片的动态
    dynamic = get_dynamic_with_multiple_images()
    if not dynamic:
        return
    
    # 打印动态信息
    print(f"动态ID: {dynamic.dynamic_id}")
    print(f"UP主: {dynamic.upstream_name}")
    print(f"类型: {dynamic.dynamic_type}")
    print(f"内容: {dynamic.content[:100]}..." if dynamic.content else "内容: 无")
    print(f"发布时间: {dynamic.publish_time}")
    print(f"图片数量: {len(dynamic.images)}")
    print(f"统计: 点赞={dynamic.stat.like}, 转发={dynamic.stat.repost}, 评论={dynamic.stat.comment}")
    print("=" * 80)
    
    # 测试企业微信通知
    test_wechat_notification(dynamic)

if __name__ == "__main__":
    main()
