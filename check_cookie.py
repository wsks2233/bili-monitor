#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie检查和保活工具

用法：
    python check_cookie.py              # 检查config.yaml中的Cookie状态
    python check_cookie.py --keepalive  # 启动保活模式
    python check_cookie.py --validate "cookie字符串"  # 验证Cookie格式
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.cookie_manager import CookieManager, CookieValidator
from bili_monitor.config import load_config
from bili_monitor.logger import setup_logger


def check_cookie_from_config():
    """检查配置文件中的Cookie"""
    logger = setup_logger(level='INFO')
    
    try:
        config = load_config('config.yaml')
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return
    
    if not config.monitor.cookie:
        print("配置文件中未设置Cookie")
        return
    
    print("=" * 50)
    print("检查Cookie状态")
    print("=" * 50)
    
    # 验证格式
    validation = CookieValidator.validate(config.monitor.cookie)
    print(f"\n格式验证: {validation['message']}")
    
    if not validation['valid']:
        print(f"缺少必要字段: {validation['missing_required']}")
        return
    
    # 检查有效性
    manager = CookieManager(
        cookie=config.monitor.cookie,
        logger=logger,
    )
    
    status = manager.check_cookie_status()
    
    print(f"\n登录状态: {'✅ 已登录' if status.is_valid else '❌ 未登录'}")
    if status.is_valid:
        print(f"用户名: {status.username}")
        print(f"UID: {status.uid}")
        print(f"VIP状态: {'是' if status.vip_status else '否'}")
        print(f"检查时间: {status.check_time}")
        
        # 估算剩余天数
        remaining = manager.get_remaining_days()
        if remaining is not None:
            print(f"预估剩余有效期: {remaining} 天")
    else:
        print(f"错误信息: {status.message}")
    
    manager.close()


def keepalive_mode():
    """保活模式"""
    logger = setup_logger(level='INFO')
    
    try:
        config = load_config('config.yaml')
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return
    
    if not config.monitor.cookie:
        print("配置文件中未设置Cookie")
        return
    
    print("=" * 50)
    print("Cookie保活模式")
    print("=" * 50)
    print("按 Ctrl+C 停止")
    print()
    
    manager = CookieManager(
        cookie=config.monitor.cookie,
        logger=logger,
        check_interval=3600,
        keepalive_interval=1800,
    )
    
    # 设置过期回调
    def on_expired(status):
        print(f"\n❌ Cookie已过期: {status.message}")
        print("请更新config.yaml中的Cookie后重启程序")
    
    manager.on_expired = on_expired
    
    # 检查初始状态
    status = manager.check_cookie_status()
    if status.is_valid:
        print(f"✅ Cookie有效 - 用户: {status.username}")
        print("启动后台保活线程...")
        manager.start_keepalive()
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止...")
    else:
        print(f"❌ Cookie无效: {status.message}")
    
    manager.close()


def validate_cookie_string(cookie: str):
    """验证Cookie字符串"""
    print("=" * 50)
    print("验证Cookie格式")
    print("=" * 50)
    
    validation = CookieValidator.validate(cookie)
    
    print(f"\n格式验证: {'✅ 有效' if validation['valid'] else '❌ 无效'}")
    print(f"详情: {validation['message']}")
    
    if validation['missing_required']:
        print(f"缺少必要字段: {validation['missing_required']}")
    
    if validation['missing_recommended']:
        print(f"建议添加字段: {validation['missing_recommended']}")
    
    # 提取SESSDATA
    sessdata = CookieValidator.extract_sessdata(cookie)
    if sessdata:
        print(f"\nSESSDATA: {sessdata[:20]}...{sessdata[-10:]}")


def main():
    parser = argparse.ArgumentParser(description='B站Cookie检查和保活工具')
    parser.add_argument('--keepalive', '-k', action='store_true', help='启动保活模式')
    parser.add_argument('--validate', '-v', type=str, help='验证Cookie字符串')
    
    args = parser.parse_args()
    
    if args.validate:
        validate_cookie_string(args.validate)
    elif args.keepalive:
        keepalive_mode()
    else:
        check_cookie_from_config()


if __name__ == '__main__':
    main()
