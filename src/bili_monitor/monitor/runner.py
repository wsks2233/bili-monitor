"""监控运行器"""

from __future__ import annotations

import logging
import random
import sys
import threading
import time
from datetime import datetime
from typing import Any, Callable

from ..api.client import BiliHTTPClient
from ..api.endpoints import BiliEndpoints, DynamicInfo, UpstreamInfo
from ..config.models import AppConfig, UpstreamConfig
from ..cookie.service import CookieService
from ..notification import NotificationBase, create_notifier
from ..storage.database import Database
from .image import ImageDownloader


class Monitor:
    """监控运行器
    
    使用示例：
        config = load_config("config.yaml")
        monitor = Monitor(config)
        monitor.run()
    """
    
    # 随机间隔配置（秒）— 运行时从 config 覆盖
    INTERVAL_CONFIG: dict[str, tuple[float, float]] = {
        "upstream_check": (2.0, 5.0),
        "user_info_fetch": (1.0, 2.5),
        "error_retry": (3.0, 6.0),
        "next_check_jitter": (0.9, 1.1),
    }
    
    def __init__(
        self,
        config: AppConfig,
        logger: logging.Logger | None = None,
        on_event: Callable[[dict], None] | None = None,
        config_path: str | None = None,
    ) -> None:
        self._config = config
        self._config_path = config_path
        self._logger = logger or logging.getLogger("bili-monitor")
        
        # 组件
        self._client: BiliHTTPClient | None = None
        self._api: BiliEndpoints | None = None
        self._db: Database | None = None
        self._cookie_service: CookieService | None = None
        self._image_downloader: ImageDownloader | None = None
        self._notifiers: list[NotificationBase] = []
        
        # 状态
        self._running = True
        self._cookie_valid = True
        self._on_event = on_event or (lambda e: None)
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器（仅在主线程中）"""
        if threading.current_thread() is not threading.main_thread():
            return
        
        import signal
        
        def signal_handler(signum: int, frame: Any) -> None:
            self._logger.info(f"收到信号 {signum}，正在停止...")
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _init_components(self) -> None:
        """初始化组件"""
        # 从配置覆盖抖动间隔
        m = self._config.monitor
        self.INTERVAL_CONFIG["upstream_check"] = (m.upstream_min, m.upstream_max)
        self.INTERVAL_CONFIG["error_retry"] = (m.error_min, m.error_max)

        # 初始化 HTTP 客户端
        self._client = BiliHTTPClient(
            cookie=self._config.monitor.cookie,
            logger=self._logger,
            rate_min=m.request_min,
            rate_max=m.request_max,
        )
        self._api = BiliEndpoints(client=self._client, logger=self._logger)
        
        # 初始化数据库
        self._db = Database(config=self._config.database, logger=self._logger)
        
        # 初始化图片下载器
        self._image_downloader = ImageDownloader(
            base_dir="images",
            logger=self._logger,
        )
        
        # 初始化 Cookie 服务
        if self._config.monitor.cookie:
            self._cookie_service = CookieService(
                cookie=self._config.monitor.cookie,
                logger=self._logger,
            )
            self._cookie_service.on_cookie_expired = self._on_cookie_expired
        
        # 初始化通知器
        self._init_notifiers()
    
    def _on_cookie_expired(self, status: Any) -> None:
        """Cookie 过期回调"""
        self._cookie_valid = False
        self._logger.error(f"Cookie 已过期: {status.message}")
        self._on_event({
            "type": "status",
            "running": self._running,
            "cookie_valid": False,
            "total_dynamics": self.get_stats().get("total_dynamics", 0) if self._db else 0,
            "total_upstreams": self.get_stats().get("total_upstreams", 0) if self._db else 0,
        })
    
    def _init_notifiers(self) -> None:
        """初始化通知器"""
        for notif_config in self._config.notification:
            try:
                notifier = create_notifier(
                    notifier_type=notif_config.type,
                    logger=self._logger,
                    webhook_url=notif_config.webhook_url,
                    secret=notif_config.secret,
                    serverchan_key=notif_config.serverchan_key,
                    pushplus_token=notif_config.pushplus_token,
                    smtp_server=notif_config.smtp_server,
                    smtp_port=notif_config.smtp_port,
                    smtp_user=notif_config.smtp_user,
                    smtp_password=notif_config.smtp_password,
                    sender=notif_config.sender,
                    receivers=notif_config.receivers,
                    bot_token=notif_config.bot_token,
                    chat_id=notif_config.chat_id,
                )
                self._notifiers.append(notifier)
                self._logger.info(f"已加载通知器: {notif_config.type}")
            except Exception as e:
                self._logger.error(f"加载通知器失败: {e}")
    
    def _random_sleep(self, min_sec: float, max_sec: float) -> None:
        """随机等待"""
        wait_time = random.uniform(min_sec, max_sec)
        self._logger.debug(f"等待 {wait_time:.2f} 秒")
        time.sleep(wait_time)
    
    def run(self) -> None:
        """运行监控"""
        self._logger.info("=" * 50)
        self._logger.info("B 站 UP 主动态监控系统启动")
        self._logger.info(f"监控 UP 主数量: {len(self._config.upstreams)}")
        self._logger.info(f"检查间隔: {self._config.monitor.check_interval} 秒")
        self._logger.info("=" * 50)

        # 校验抖动配置
        for w in self._config.monitor.validate():
            self._logger.warning(w)

        if not self._config.upstreams:
            self._logger.warning("没有配置要监控的 UP 主，程序退出")
            return

        # 初始化组件
        self._init_components()
        
        # 检查 Cookie 状态
        if self._cookie_service:
            status = self._cookie_service.check_status()
            if status.is_valid:
                self._logger.info(f"Cookie 有效 - 用户: {status.username}")
                self._cookie_service.start_keepalive()
            else:
                self._logger.warning(f"Cookie 状态: {status.message}")
        
        # 更新 UP 主信息
        for upstream in self._config.upstreams:
            self._update_upstream_info(upstream)
            self._random_sleep(*self.INTERVAL_CONFIG["upstream_check"])
        
        # 主循环
        try:
            while self._running:
                self._check_all_upstreams()
                self._on_event({
                    "type": "status",
                    "running": self._running,
                    "cookie_valid": self._cookie_valid,
                    "total_dynamics": self.get_stats().get("total_dynamics", 0) if self._db else 0,
                    "total_upstreams": self.get_stats().get("total_upstreams", 0) if self._db else 0,
                })
                self._wait_for_next_check()
        except Exception as e:
            self._logger.error(f"监控过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._cleanup()
    
    def _update_upstream_info(self, upstream_config: UpstreamConfig) -> None:
        """更新 UP 主信息"""
        self._logger.info(f"更新 UP 主信息: {upstream_config.uid}")

        try:
            user_info = self._api.get_user_info(upstream_config.uid)
            if user_info:
                self._random_sleep(*self.INTERVAL_CONFIG["user_info_fetch"])
                fans = self._api.get_user_fans(upstream_config.uid)
                user_info.fans = fans

                if user_info.name and user_info.name != upstream_config.name:
                    self._logger.info(f"UP 主名称更新: {upstream_config.name} -> {user_info.name}")

                # 下载头像到本地缓存
                if user_info.face and self._image_downloader:
                    local_face = self._image_downloader.download_avatar(user_info.face, upstream_config.uid)
                    if local_face:
                        user_info.face = local_face
                        # 同步更新 config 对象中的 face
                        for u in self._config.upstreams:
                            if u.uid == upstream_config.uid:
                                u.face = local_face
                                break

                self._db.save_upstream(user_info)

                # 保存配置到文件（同步 face 到 config.yaml）
                if self._config_path:
                    try:
                        from ..config.loader import save_config
                        save_config(self._config, self._config_path)
                    except Exception as e:
                        self._logger.warning(f"保存配置文件失败: {e}")
                self._logger.info(f"UP 主信息: {user_info.name}, 粉丝: {fans}")
        except Exception as e:
            self._logger.error(f"更新 UP 主 {upstream_config.uid} 信息失败: {e}")
            import traceback
            self._logger.debug(traceback.format_exc())
            self._random_sleep(*self.INTERVAL_CONFIG["error_retry"])
    
    def _check_all_upstreams(self) -> None:
        """检查所有 UP 主"""
        self._logger.info("-" * 40)
        self._logger.info(f"开始检查动态更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self._cookie_service and not self._cookie_valid:
            # 重新检查 Cookie（之前可能是网络抖动导致误判）
            try:
                status = self._cookie_service.check_status()
                if status.is_valid:
                    self._cookie_valid = True
                    self._logger.info("Cookie 状态已恢复")
                else:
                    self._logger.warning(f"Cookie 仍不可用: {status.message}，跳过本轮")
                    return
            except Exception as e:
                self._logger.warning(f"Cookie 检查失败: {e}，跳过本轮")
                return
        
        for i, upstream in enumerate(self._config.upstreams):
            if not self._running:
                break
            self._check_upstream(upstream)
            if i < len(self._config.upstreams) - 1:
                self._random_sleep(*self.INTERVAL_CONFIG["upstream_check"])
        
        self._logger.info("本轮检查完成")
    
    def _check_upstream(self, upstream: UpstreamConfig) -> None:
        """检查单个 UP 主"""
        self._logger.info(f"检查 UP 主: {upstream.name} (UID: {upstream.uid})")
        
        processed_ids = self._db.get_processed_ids(upstream.uid)
        dynamics = self._api.get_user_dynamics(upstream.uid)
        
        if not dynamics:
            self._logger.info("未获取到动态数据")
            return
        
        new_count = 0
        for dynamic in dynamics:
            if dynamic.dynamic_id not in processed_ids:
                if self._process_new_dynamic(dynamic, upstream.name):
                    new_count += 1
                    self._random_sleep(0.5, 1.5)
        
        self._logger.info(f"发现 {new_count} 条新动态")
    
    def _process_new_dynamic(self, dynamic: DynamicInfo, upstream_name: str) -> bool:
        """处理新动态"""
        self._logger.info(f"发现新动态: {dynamic.dynamic_id}")
        self._logger.info(f"  类型: {dynamic.dynamic_type}")

        content_display = dynamic.content[:100] + "..." if len(dynamic.content) > 100 else dynamic.content
        self._logger.info(f"  内容: {content_display}")

        if dynamic.video:
            self._logger.info(f"  视频: {dynamic.video.title}")

        if dynamic.images:
            self._logger.info(f"  图片: {len(dynamic.images)} 张")
            self._download_images(dynamic, upstream_name)

        self._logger.info(
            f"  互动: 点赞 {dynamic.stat.like}, "
            f"转发 {dynamic.stat.repost}, "
            f"评论 {dynamic.stat.comment}"
        )

        # 快照当前 UP 主头像到动态记录
        upstream = self._db.get_upstream(dynamic.uid)
        if upstream and upstream.face:
            dynamic.face = upstream.face

        if self._db.save_dynamic(dynamic):
            self._send_notification(dynamic)
            return True

        return False
    
    def _download_images(self, dynamic: DynamicInfo, upstream_name: str) -> None:
        """下载动态图片"""
        if not dynamic.images or not self._image_downloader:
            return
        
        for i, img in enumerate(dynamic.images):
            self._image_downloader.download(
                url=img.url,
                upstream_name=upstream_name,
                dynamic_id=dynamic.dynamic_id,
                index=i,
            )
    
    def _send_notification(self, dynamic: DynamicInfo) -> None:
        """发送通知"""
        if not self._notifiers:
            return
        
        for notifier in self._notifiers:
            try:
                result = notifier.send(dynamic)
                if result.success:
                    self._logger.info(f"通知发送成功: {result.message}")
                else:
                    self._logger.warning(f"通知发送失败: {result.message}")
            except Exception as e:
                self._logger.error(f"通知发送异常: {e}")
    
    def _wait_for_next_check(self) -> None:
        """等待下一轮检查"""
        interval = self._config.monitor.check_interval
        jitter = random.uniform(*self.INTERVAL_CONFIG["next_check_jitter"])
        actual_interval = int(interval * jitter)
        
        self._logger.info(f"等待 {actual_interval} 秒后进行下一轮检查...")
        
        start_time = time.time()
        while self._running and (time.time() - start_time) < actual_interval:
            time.sleep(1)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._logger.info("正在清理资源...")
        
        if self._cookie_service:
            self._cookie_service.close()
        
        if self._client:
            self._client.close()
        
        if self._db:
            self._db.close()
        
        self._logger.info("监控已停止")
    
    def stop(self) -> None:
        """停止监控"""
        self._running = False
        self._on_event({
            "type": "status",
            "running": False,
            "cookie_valid": self._cookie_valid,
            "total_dynamics": self.get_stats().get("total_dynamics", 0) if self._db else 0,
            "total_upstreams": self.get_stats().get("total_upstreams", 0) if self._db else 0,
        })
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if self._db:
            return self._db.get_stats()
        return {}
    
    def get_dynamics(
        self,
        uid: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """获取动态列表"""
        if self._db:
            return self._db.get_dynamics(uid, limit, offset)
        return []
    
    def get_cookie_status(self) -> dict[str, Any]:
        """获取 Cookie 状态"""
        if not self._cookie_service:
            return {"valid": False, "message": "未配置 Cookie"}
        
        status = self._cookie_service.check_status()
        return {
            "valid": status.is_valid,
            "username": status.username,
            "uid": status.uid,
            "check_time": status.check_time,
            "message": status.message,
        }
