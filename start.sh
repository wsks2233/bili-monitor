#!/bin/bash
# 启动脚本：默认仅启动 Web；监控通过 UI「启动」或单独 bili-monitor monitor
# 文件锁（data/bili_monitor.lock）保证不会双开监控。

PORT="${WEB_PORT:-8000}"

echo "启动 Web 服务 (端口 ${PORT})..."
bili-monitor web --host 0.0.0.0 --port "${PORT}" &
WEB_PID=$!

cleanup() {
    echo "停止服务..."
    kill $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Web 服务: http://0.0.0.0:${PORT}"
if [ "${START_MONITOR:-0}" = "1" ]; then
    echo "启动监控服务 (START_MONITOR=1)..."
    bili-monitor monitor &
    MONITOR_PID=$!
    echo "监控服务: 运行中（与 Web 同容器；文件锁防双开）"
    wait $WEB_PID $MONITOR_PID
else
    echo "监控服务: 未自动启动（在 Web UI 中启动，或另开 bili-monitor monitor）"
    wait $WEB_PID
fi
