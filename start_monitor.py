#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动监控服务脚本
"""

import sys
import os
import logging
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config
from bili_monitor.core.logger import setup_logger
from bili_monitor.monitor import Monitor

def main():
    print("=" * 70)
    print("B 站 UP 主动态监控服务")
    print("=" * 70)
    
    # 加载配置
    print("\n[1/4] 加载配置文件...")
    config_path = "config.yaml"
    try:
        config = load_config(config_path)
        print(f"✓ 配置加载成功")
        print(f"  - UP 主数量：{len(config.upstreams)}")
        print(f"  - 检查间隔：{config.monitor.check_interval}秒")
    except Exception as e:
        print(f"✗ 配置加载失败：{e}")
        return False
    
    # 初始化日志
    print("\n[2/4] 初始化日志系统...")
    try:
        logger = setup_logger(config.logger)
        print(f"✓ 日志初始化成功")
        print(f"  - 日志级别：{config.logger.level}")
        print(f"  - 日志文件：{config.logger.file}")
    except Exception as e:
        print(f"✗ 日志初始化失败：{e}")
        return False
    
    # 创建监控实例
    print("\n[3/4] 创建监控实例...")
    try:
        monitor = Monitor(config, logger)
        print(f"✓ 监控实例创建成功")
        print(f"  - Cookie 状态：{'已设置' if config.monitor.cookie else '未设置'}")
        print(f"  - 通知方式：{len(config.notification) if config.notification else 0}种")
    except Exception as e:
        print(f"✗ 监控实例创建失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 启动监控
    print("\n[4/4] 启动监控服务...")
    print("=" * 70)
    print("\n监控服务已启动，按 Ctrl+C 停止\n")
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n\n收到停止信号，正在关闭监控服务...")
        monitor._cleanup()
        print("✓ 监控服务已停止")
    
    return True

if __name__ == "__main__":
    try:
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n启动失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
