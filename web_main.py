#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.cli import run_web


def main():
    parser = argparse.ArgumentParser(description='B站UP主动态监控系统 - Web界面')
    parser.add_argument('--host', type=str, default=None, help='监听地址')
    parser.add_argument('--port', type=int, default=None, help='监听端口')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')

    args = parser.parse_args()

    run_web(config_path=args.config, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
