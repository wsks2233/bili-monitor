#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动监控服务脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.cli import run_monitor


def main():
    print("=" * 70)
    print("B 站 UP 主动态监控服务")
    print("=" * 70)

    config_path = "config.yaml"
    run_monitor(config_path, verbose=True)
    return True


if __name__ == "__main__":
    try:
        os.makedirs('logs', exist_ok=True)
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n启动失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
