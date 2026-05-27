#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.cli import run_monitor


def main():
    try:
        run_monitor("config.yaml")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请先复制 config.example.yaml 为 config.yaml 并进行配置")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
