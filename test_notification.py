# -*- coding: utf-8 -*-
"""
通知测试脚本

用于测试各种通知渠道是否正常工作
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bili_monitor.core.config import load_config
from bili_monitor.notification.wechat import WeChatNotifier
from bili_monitor.notification.email import EmailNotifier
from bili_monitor.core.models import DynamicInfo, StatInfo, VideoInfo


def create_test_dynamic():
    """创建测试动态数据"""
    return DynamicInfo(
        dynamic_id="test_1234567890",
        uid="546195",
        upstream_name="老番茄（测试）",
        dynamic_type="图文",
        content="这是一条测试消息，用于验证通知功能是否正常工作。如果您收到此消息，说明通知配置成功！",
        publish_time=datetime.now(),
        images=[],
        video=None,
        stat=StatInfo(
            like=100,
            repost=50,
            comment=30
        ),
        raw_json={}
    )


def test_wechat_notification(config):
    """测试企业微信通知"""
    print("\n" + "="*60)
    print("📱 测试企业微信通知")
    print("="*60)
    
    for notif_config in config.notification:
        if notif_config.get('type') == 'wechat':
            webhook_url = notif_config.get('webhook_url', '')
            
            if not webhook_url:
                print("❌ 未配置企业微信 webhook_url")
                return False
            
            print(f"📡 Webhook URL: {webhook_url[:50]}...")
            
            notifier = WeChatNotifier(webhook_url=webhook_url)
            
            print("🧪 发送测试消息...")
            test_dynamic = create_test_dynamic()
            result = notifier.send(test_dynamic)
            
            if result.success:
                print(f"✅ {result.message}")
                return True
            else:
                print(f"❌ {result.message}")
                return False
    
    print("⚠️  未找到企业微信通知配置")
    return False


def test_email_notification(config):
    """测试邮件通知"""
    print("\n" + "="*60)
    print("📧 测试邮件通知")
    print("="*60)
    
    for notif_config in config.notification:
        if notif_config.get('type') == 'email':
            smtp_server = notif_config.get('smtp_server', '')
            smtp_port = notif_config.get('smtp_port', 465)
            smtp_user = notif_config.get('smtp_user', '')
            smtp_password = notif_config.get('smtp_password', '')
            sender = notif_config.get('sender', '')
            receivers = notif_config.get('receivers', [])
            use_ssl = notif_config.get('use_ssl', True)
            
            print(f"📡 SMTP 服务器: {smtp_server}:{smtp_port}")
            print(f"👤 发送者: {sender}")
            print(f"📥 接收者: {', '.join(receivers)}")
            
            if not receivers:
                print("❌ 未配置邮件接收者")
                return False
            
            notifier = EmailNotifier(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_user=smtp_user,
                smtp_password=smtp_password,
                sender=sender,
                receivers=receivers,
                use_ssl=use_ssl
            )
            
            print("🧪 发送测试邮件...")
            result = notifier.test()
            
            if result:
                print("✅ 邮件通知测试成功")
                return True
            else:
                print("❌ 邮件通知测试失败")
                return False
    
    print("⚠️  未找到邮件通知配置")
    return False


def main():
    """主函数"""
    print("\n" + "🔔 B站动态监控系统 - 通知测试".center(60, "="))
    
    try:
        config = load_config()
        print(f"✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return
    
    print(f"\n📋 已配置的通知方式:")
    for notif in config.notification:
        print(f"   - {notif.get('type', 'unknown')}")
    
    results = {}
    
    if any(n.get('type') == 'wechat' for n in config.notification):
        results['wechat'] = test_wechat_notification(config)
    
    if any(n.get('type') == 'email' for n in config.notification):
        results['email'] = test_email_notification(config)
    
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:12s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有通知测试通过！")
    else:
        print("\n⚠️  部分通知测试失败，请检查配置")


if __name__ == '__main__':
    main()
