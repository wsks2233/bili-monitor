#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.core.config import load_config
from bili_monitor.web import start_web_server


def main():
    parser = argparse.ArgumentParser(description='B站UP主动态监控系统 - Web界面')
    parser.add_argument('--host', type=str, default=None, help='监听地址')
    parser.add_argument('--port', type=int, default=None, help='监听端口')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    host = args.host if args.host else config.web.host
    port = args.port if args.port else config.web.port
    
    print(f"启动Web服务: http://{host}:{port}")
    start_web_server(host=host, port=port)


if __name__ == "__main__":
    main()
