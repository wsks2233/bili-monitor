#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试企业微信应用通知功能
"""

import sys
import os
import logging
from datetime import datetime
from bili_monitor.core.models import DynamicInfo, StatInfo, ImageInfo
from bili_monitor.notification.wechat import WeChatNotifier

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_wechat_app():
    """测试企业微信应用通知功能"""
    logger.info("开始测试企业微信应用通知功能...")
    
    # 创建测试动态信息
    test_dynamic = DynamicInfo(
        dynamic_id="123456",
        uid="1039025435",
        upstream_name="测试UP主",
        dynamic_type="图文",
        content="这是一条测试动态，用于验证企业微信应用通知功能是否正常工作。",
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
    
    # 企业微信机器人webhook配置
    wechat_config = {
        "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fa563bd2-035c-448c-b87a-1c9c02832a5a"  # 用户提供的webhook地址
    }
    
    logger.info(f"企业微信配置: webhook_url={wechat_config['webhook_url']}")
    
    # 创建微信通知器
    wechat_notifier = WeChatNotifier(**wechat_config)
    
    # 测试发送通知
    logger.info("发送测试通知...")
    try:
        result = wechat_notifier.send(test_dynamic)
        if result.success:
            logger.info(f"✅ 测试成功：{result.message}")
            print(f"✅ 测试成功：{result.message}")
        else:
            logger.error(f"❌ 测试失败：{result.message}")
            print(f"❌ 测试失败：{result.message}")
        return result.success
    except Exception as e:
        logger.error(f"❌ 测试异常：{e}", exc_info=True)
        print(f"❌ 测试异常：{e}")
        return False

if __name__ == "__main__":
    test_wechat_app()

