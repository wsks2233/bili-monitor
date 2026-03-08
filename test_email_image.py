#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邮件发送图片功能
"""

import sys
import os
from datetime import datetime
from bili_monitor.core.models import DynamicInfo, ImageInfo, StatInfo
from bili_monitor.notification.email import EmailNotifier

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_image():
    """测试邮件发送图片功能"""
    print("测试邮件发送图片功能...")
    
    # 创建测试动态信息
    test_dynamic = DynamicInfo(
        dynamic_id="123456",
        uid="1039025435",
        upstream_name="测试UP主",
        dynamic_type="图文",
        content="这是一条带有图片的测试动态",
        publish_time=datetime.now(),
        images=[
            ImageInfo(
                url="https://i0.hdslb.com/bfs/face/member/noface.jpg",
                width=1280,
                height=720
            )
        ],
        stat=StatInfo(like=100, comment=50, repost=20)
    )
    
    # 邮件配置（使用之前的配置）
    email_config = {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "smtp_user": "flowers2233@foxmail.com",
        "smtp_password": "owkcemrmpigebiaf",
        "sender": "flowers2233@foxmail.com",
        "receivers": ["flowers2233@foxmail.com"]
    }
    
    # 创建邮件通知器
    email_notifier = EmailNotifier(**email_config)
    
    # 发送测试邮件
    print("发送测试邮件...")
    result = email_notifier.send(test_dynamic)
    
    if result.success:
        print("✅ 测试成功：" + result.message)
    else:
        print("❌ 测试失败：" + result.message)
    
    return result.success

if __name__ == "__main__":
    test_email_image()
