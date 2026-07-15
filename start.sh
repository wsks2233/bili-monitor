#!/bin/bash
# 启动脚本：同时运行 Web 服务和监控服务

echo "启动 Web 服务..."
bili-monitor web --host 0.0.0.0 --port 8000 &
WEB_PID=$!

echo "启动监控服务..."
bili-monitor monitor &
MONITOR_PID=$!

# 捕获退出信号
cleanup() {
    echo "停止服务..."
    kill $WEB_PID $MONITOR_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "所有服务已启动"
echo "  - Web 服务: http://0.0.0.0:8000"
echo "  - 监控服务: 运行中"

# 等待任意子进程退出
wait
