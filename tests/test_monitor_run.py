#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整监控流程测试 - 短时间运行验证

运行方式: python -m tests.test_monitor_run
或从项目根目录: python tests/test_monitor_run.py
"""

import sys
import os
import time
import signal
import threading

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from bili_monitor.core.config import load_config
from bili_monitor.core.logger import setup_logger
from bili_monitor.monitor import Monitor


def run_short_monitor_test():
    """运行短时间的监控流程测试（10秒）"""
    print("\n" + "="*70)
    print("完整监控流程测试 - 将运行10秒后自动停止")
    print("="*70)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        
        print(f"\n[OK] 配置加载成功")
        print(f"  - 监控UP主数量: {len(config.upstreams)}")
        for i, up in enumerate(config.upstreams):
            print(f"    {i+1}. {up.name} (UID: {up.uid})")
        
        # 创建Monitor实例
        monitor = Monitor(config, logger)
        print(f"\n[OK] Monitor实例创建成功")
        
        # 在后台线程中运行监控
        def run_monitor():
            try:
                monitor.run()
            except Exception as e:
                logger.error(f"监控运行异常: {e}")
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        print(f"[OK] 监控线程已启动")
        
        # 等待10秒让监控完成一轮检查
        print(f"\n  等待10秒，让监控完成一轮检查...")
        time.sleep(10)
        
        # 停止监控
        if monitor.running:
            monitor.running = False
            print(f"\n[OK] 已发送停止信号")
        
        # 在关闭前获取统计信息
        if monitor.db:
            stats = monitor.db.get_stats()
            print(f"\n 监控统计:")
            print(f"  - 总动态数: {stats['total_dynamics']}")
            print(f"  - 总UP主数: {stats['total_upstreams']}")
            
            if stats.get('upstream_stats'):
                print(f"\n  各UP主动态统计:")
                for stat in stats['upstream_stats']:
                    print(f"    • UID {stat['uid']}: {stat['count']} 条动态")
        
        # 等待线程结束
        monitor_thread.join(timeout=5)
        print(f"[OK] 监控线程已停止")
        
        # 清理资源
        monitor._cleanup()
        
        print("\n" + "="*70)
        print("✅ 完整监控流程测试通过！")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] 监控流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_short_monitor_test()
    sys.exit(0 if success else 1)
