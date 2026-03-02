#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config
from bili_monitor.core.logger import setup_logger
from bili_monitor.monitor import Monitor


def main():
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        monitor = Monitor(config, logger)
        monitor.run()
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
