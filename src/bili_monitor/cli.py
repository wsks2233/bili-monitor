"""CLI 入口"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config.loader import load_config
from .config.models import AppConfig


def setup_logger(config: AppConfig) -> logging.Logger:
    """设置日志"""
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger("bili-monitor")
    logger.setLevel(getattr(logging, config.logger.level.upper(), logging.INFO))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.logger.level.upper(), logging.INFO))
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_dir = Path(config.logger.file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        config.logger.file,
        maxBytes=config.logger.max_bytes,
        backupCount=config.logger.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, config.logger.level.upper(), logging.INFO))
    file_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


def run_monitor(config_path: str, verbose: bool = False) -> None:
    """运行监控"""
    try:
        config = load_config(config_path)
        logger = setup_logger(config)
        
        if verbose:
            print("=" * 70)
            print("B 站 UP 主动态监控服务")
            print("=" * 70)
            print(f"\n配置文件: {config_path}")
            print(f"UP 主数量: {len(config.upstreams)}")
            print(f"检查间隔: {config.monitor.check_interval} 秒")
            print(f"Cookie 状态: {'已设置' if config.monitor.cookie else '未设置'}")
            print(f"通知方式: {len(config.notification)} 种")
            print("\n" + "=" * 70)
        
        from .monitor.runner import Monitor
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


def run_web(config_path: str, host: str | None = None, port: int | None = None) -> None:
    """运行 Web 服务"""
    try:
        config = load_config(config_path)
        logger = setup_logger(config)
        
        from .web.app import create_app
        app = create_app(config_path)
        
        # 存储配置到 app
        app.config["APP_CONFIG"] = config
        
        # 启动 Web 服务
        actual_host = host or config.web.host
        actual_port = port or config.web.port
        
        print(f"启动 Web 服务: http://{actual_host}:{actual_port}")
        app.run(host=actual_host, port=actual_port, debug=False)
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请先复制 config.example.yaml 为 config.yaml 并进行配置")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """主入口"""
    parser = argparse.ArgumentParser(
        description="B站UP主动态监控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  bili-monitor monitor              # 运行监控
  bili-monitor monitor -v           # 运行监控（详细输出）
  bili-monitor web                  # 运行 Web 服务
  bili-monitor web --port 8000      # 运行 Web 服务（指定端口）
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # monitor 命令
    monitor_parser = subparsers.add_parser("monitor", help="运行监控")
    monitor_parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)",
    )
    monitor_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出",
    )
    
    # web 命令
    web_parser = subparsers.add_parser("web", help="运行 Web 服务")
    web_parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)",
    )
    web_parser.add_argument(
        "--host",
        help="监听地址 (默认: 配置文件中的值)",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        help="监听端口 (默认: 配置文件中的值)",
    )
    
    args = parser.parse_args()
    
    if args.command == "monitor":
        run_monitor(args.config, args.verbose)
    elif args.command == "web":
        run_web(args.config, args.host, args.port)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
