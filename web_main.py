#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.web import start_web_server


def main():
    parser = argparse.ArgumentParser(description='B站UP主动态监控系统 - Web界面')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8000, help='监听端口')
    
    args = parser.parse_args()
    
    print(f"启动Web服务: http://{args.host}:{args.port}")
    start_web_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
