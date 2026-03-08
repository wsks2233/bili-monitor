#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件通知时间格式测试
验证邮件通知的时间格式和位置修改是否生效
"""

import sys
import os
import yaml
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.models import DynamicInfo, StatInfo, UpstreamInfo, ImageInfo, VideoInfo
from bili_monitor.notification.email import EmailNotifier

def print_banner(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def load_config():
    """加载配置文件"""
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ 配置文件 {config_path} 不存在")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ 加载配置失败：{e}")
        return None

def create_test_dynamic():
    """创建测试动态对象"""
    # 创建一个测试动态，时间设为5分钟前
    test_time = datetime.now() - timedelta(minutes=5)
    
    dynamic = DynamicInfo(
        dynamic_id="test_123456789",
        uid="1039025435",
        upstream_name="战国时代_姜汁汽水",
        dynamic_type="图文",
        content="这是一条测试动态，用于验证邮件通知的时间格式和位置修改是否生效。\n\n测试内容测试内容测试内容测试内容测试内容测试内容测试内容测试内容测试内容测试内容测试内容测试内容。",
        publish_time=test_time,
        create_time=test_time,
        stat=StatInfo(
            like=123,
            repost=45,
            comment=67
        ),
        images=[
            ImageInfo(
                url="http://i0.hdslb.com/bfs/new_dyn/4d686b213abfece77f.jpg",
                width=800,
                height=600
            )
        ],
        video=None,
        raw_json={}
    )
    
    return dynamic

def test_email_notification(config):
    """测试邮件通知"""
    if not config or 'notification' not in config:
        print("❌ 配置中未找到通知设置")
        return False
    
    # 找到邮件通知配置
    email_config = None
    for notifier_config in config['notification']:
        if notifier_config.get('type') == 'email':
            email_config = notifier_config
            break
    
    if not email_config:
        print("❌ 配置中未找到邮件通知设置")
        return False
    
    print("📧 邮件配置信息:")
    print(f"  SMTP 服务器: {email_config.get('smtp_server')}")
    print(f"  端口: {email_config.get('smtp_port')}")
    print(f"  发件人: {email_config.get('smtp_user')}")
    print(f"  收件人: {', '.join(email_config.get('receivers', []))}")
    print()
    
    # 创建邮件通知器
    notifier_config = email_config.copy()
    notifier_config.pop('type', None)  # 移除 type 键
    
    try:
        notifier = EmailNotifier(**notifier_config)
        print("✓ 邮件通知器创建成功")
    except Exception as e:
        print(f"❌ 邮件通知器创建失败：{e}")
        return False
    
    # 创建测试动态
    dynamic = create_test_dynamic()
    print(f"\n📅 测试动态时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   动态类型: {dynamic.dynamic_type}")
    print(f"   UP 主: {dynamic.upstream_name}")
    print(f"   内容: {dynamic.content[:50]}...")
    print()
    
    # 预览邮件内容
    print_banner("邮件内容预览")
    print("【纯文本内容】")
    print(notifier._format_simple_text(dynamic))
    print()
    print("【HTML 内容】")
    print(notifier._format_simple_html(dynamic))
    print()
    
    # 测试发送
    print_banner("测试邮件发送")
    print("正在发送测试邮件...")
    result = notifier.send(dynamic)
    
    if result.success:
        print(f"✅ 测试成功：{result.message}")
        print()
        print("💡 请检查以下内容：")
        print("  1. 邮件是否收到")
        print("  2. 时间显示格式是否正确")
        print("  3. 时间位置是否按预期修改")
        print("  4. 其他内容是否正常")
        return True
    else:
        print(f"❌ 测试失败：{result.message}")
        return False

def main():
    print_banner("邮件通知时间格式测试")
    
    # 加载配置
    config = load_config()
    if not config:
        return False
    
    # 测试邮件通知
    success = test_email_notification(config)
    
    print_banner("测试完成")
    if success:
        print("🎉 测试成功！请检查邮箱确认时间格式和位置修改是否生效。")
    else:
        print("⚠️  测试失败，请检查配置和网络连接。")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
