# -*- coding: utf-8 -*-

import logging
import time
import signal
import sys
import os
import random
from typing import List, Set, Optional
from datetime import datetime

from .core.config import Config, UpstreamConfig
from .api.bili_api import BiliAPI
from .api.cookie_manager import CookieManager, CookieValidator
from .storage.database import Database, create_database
from .core.models import DynamicInfo, UpstreamInfo
from .notification import create_notifier


class Monitor:
    # 随机间隔配置（秒）
    INTERVAL_CONFIG = {
        'upstream_check': (2.0, 5.0),
        'user_info_fetch': (1.0, 2.5),
        'error_retry': (3.0, 6.0),
        'next_check_jitter': (0.9, 1.1),
    }
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger('bili-monitor')
        self.api = BiliAPI(self.logger, cookie=config.monitor.cookie)
        self.db: Optional[Database] = None
        self.running = True
        self.image_dir = "images"
        
        # Cookie管理器
        self.cookie_manager: Optional[CookieManager] = None
        self._cookie_valid = True
        
        # 通知器列表
        self.notifiers: List = []
        
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，正在停止...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _init_database(self) -> None:
        self.db = create_database(self.config.database, self.logger)
    
    def _random_sleep(self, min_sec: float, max_sec: float):
        """随机等待"""
        wait_time = random.uniform(min_sec, max_sec)
        self.logger.debug(f"等待 {wait_time:.2f} 秒")
        time.sleep(wait_time)
    
    def _init_cookie_manager(self) -> bool:
        """初始化Cookie管理器"""
        if not self.config.monitor.cookie:
            self.logger.warning("未配置Cookie，部分功能可能受限")
            return False
        
        validation = CookieValidator.validate(self.config.monitor.cookie)
        if not validation['valid']:
            self.logger.error(f"Cookie格式无效: {validation['message']}")
            return False
        
        self.logger.info(f"Cookie验证: {validation['message']}")
        
        self.cookie_manager = CookieManager(
            cookie=self.config.monitor.cookie,
            logger=self.logger,
            config_path="data/cookie_status.json",
            check_interval=3600,
            keepalive_interval=1800,
        )
        
        def on_cookie_expired(status):
            self._cookie_valid = False
            self.logger.error(f"Cookie已过期: {status.message}")
            self.logger.error("请更新config.yaml中的Cookie后重启程序")
        
        self.cookie_manager.on_expired = on_cookie_expired
        
        status = self.cookie_manager.check_cookie_status()
        if status.is_valid:
            self.logger.info(f"Cookie有效 - 用户: {status.username} (UID: {status.uid})")
            self.cookie_manager.start_keepalive()
            return True
        else:
            self.logger.error(f"Cookie无效: {status.message}")
            return False
    
    def _init_notifiers(self) -> None:
        """初始化通知器"""
        notification_config = getattr(self.config, 'notification', None)
        if not notification_config:
            return
        
        for notifier_cfg in notification_config:
            try:
                notifier = create_notifier(
                    notifier_cfg.get('type', ''),
                    **notifier_cfg
                )
                self.notifiers.append(notifier)
                self.logger.info(f"已加载通知器: {notifier_cfg.get('type')}")
            except Exception as e:
                self.logger.error(f"加载通知器失败: {e}")
    
    def run(self) -> None:
        self.logger.info("=" * 50)
        self.logger.info("B站UP主动态监控系统启动")
        self.logger.info(f"监控UP主数量: {len(self.config.upstreams)}")
        self.logger.info(f"检查间隔: {self.config.monitor.check_interval} 秒")
        self.logger.info("=" * 50)
        
        if not self.config.upstreams:
            self.logger.warning("没有配置要监控的UP主，程序退出")
            return
        
        cookie_ok = self._init_cookie_manager()
        if not cookie_ok and self.config.monitor.cookie:
            self.logger.warning("Cookie验证失败，将尝试使用备用方案")
        
        self._init_database()
        self._init_notifiers()
        
        for upstream in self.config.upstreams:
            self._update_upstream_info(upstream)
            self._random_sleep(*self.INTERVAL_CONFIG['upstream_check'])
        
        try:
            while self.running:
                self._check_all_upstreams()
                self._wait_for_next_check()
        except Exception as e:
            self.logger.error(f"监控过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._cleanup()
    
    def _update_upstream_info(self, upstream_config: UpstreamConfig) -> None:
        self.logger.info(f"更新UP主信息: {upstream_config.uid}")
        
        try:
            user_info = self.api.get_user_info(upstream_config.uid)
            if user_info:
                self._random_sleep(*self.INTERVAL_CONFIG['user_info_fetch'])
                fans = self.api.get_user_fans(upstream_config.uid)
                user_info.fans = fans
                
                if not upstream_config.name:
                    upstream_config.name = user_info.name
                
                self.db.save_upstream(user_info)
                self.logger.info(f"UP主信息: {user_info.name}, 粉丝: {fans}")
        except Exception as e:
            self.logger.error(f"更新UP主 {upstream_config.uid} 信息失败: {e}")
            self._random_sleep(*self.INTERVAL_CONFIG['error_retry'])
    
    def _check_all_upstreams(self) -> None:
        self.logger.info("-" * 40)
        self.logger.info(f"开始检查动态更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.cookie_manager and not self._cookie_valid:
            self.logger.warning("Cookie已失效，跳过本轮检查")
            return
        
        for i, upstream in enumerate(self.config.upstreams):
            if not self.running:
                break
            self._check_upstream(upstream)
            if i < len(self.config.upstreams) - 1:
                self._random_sleep(*self.INTERVAL_CONFIG['upstream_check'])
        
        self.logger.info("本轮检查完成")
    
    def _check_upstream(self, upstream: UpstreamConfig) -> None:
        self.logger.info(f"检查UP主: {upstream.name} (UID: {upstream.uid})")
        
        processed_ids = self.db.get_processed_ids(upstream.uid)
        dynamics = self.api.get_user_dynamics(upstream.uid)
        
        if not dynamics:
            self.logger.info(f"未获取到动态数据")
            return
        
        new_count = 0
        for dynamic in dynamics:
            if dynamic.dynamic_id not in processed_ids:
                if self._process_new_dynamic(dynamic, upstream.name):
                    new_count += 1
                    self._random_sleep(0.5, 1.5)
        
        self.logger.info(f"发现 {new_count} 条新动态")
    
    def _process_new_dynamic(self, dynamic: DynamicInfo, upstream_name: str = "") -> bool:
        self.logger.info(f"发现新动态: {dynamic.dynamic_id}")
        self.logger.info(f"  类型: {dynamic.dynamic_type}")
        content_display = dynamic.content[:100] + "..." if len(dynamic.content) > 100 else dynamic.content
        self.logger.info(f"  内容: {content_display}")
        
        if dynamic.video:
            self.logger.info(f"  视频: {dynamic.video.title}")
        
        if dynamic.images:
            self.logger.info(f"  图片: {len(dynamic.images)} 张")
            self._download_images(dynamic, upstream_name)
        
        self.logger.info(f"  互动: 点赞 {dynamic.stat.like}, 转发 {dynamic.stat.repost}, 评论 {dynamic.stat.comment}")
        
        if self.db.save_dynamic(dynamic):
            self._send_notification(dynamic)
            return True
        
        return False
    
    def _download_images(self, dynamic: DynamicInfo, upstream_name: str) -> None:
        if not dynamic.images:
            return
        
        safe_name = "".join(c for c in upstream_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = dynamic.uid
        
        dynamic_dir = os.path.join(self.image_dir, safe_name, dynamic.dynamic_id)
        
        for i, img in enumerate(dynamic.images):
            ext = '.jpg'
            if '?' in img.url:
                base_url = img.url.split('?')[0]
                if '.' in base_url:
                    ext = '.' + base_url.rsplit('.', 1)[-1]
            
            filename = f"{i+1:03d}{ext}"
            save_path = os.path.join(dynamic_dir, filename)
            
            if os.path.exists(save_path):
                self.logger.info(f"  图片已存在: {save_path}")
                continue
            
            self.logger.info(f"  下载图片: {img.url[:50]}...")
            if self.api.download_image(img.url, save_path):
                self.logger.info(f"  保存到: {save_path}")
            else:
                self.logger.error(f"  图片下载失败")
    
    def _send_notification(self, dynamic: DynamicInfo) -> None:
        """发送通知"""
        if not self.notifiers:
            return
        
        for notifier in self.notifiers:
            try:
                result = notifier.send(dynamic)
                if result.success:
                    self.logger.info(f"通知发送成功: {result.message}")
                else:
                    self.logger.warning(f"通知发送失败: {result.message}")
            except Exception as e:
                self.logger.error(f"通知发送异常: {e}")
    
    def _wait_for_next_check(self) -> None:
        interval = self.config.monitor.check_interval
        jitter = random.uniform(*self.INTERVAL_CONFIG['next_check_jitter'])
        actual_interval = int(interval * jitter)
        
        self.logger.info(f"等待 {actual_interval} 秒后进行下一轮检查...")
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < actual_interval:
            time.sleep(1)
    
    def _cleanup(self) -> None:
        self.logger.info("正在清理资源...")
        
        if self.cookie_manager:
            self.cookie_manager.close()
        
        if self.api:
            self.api.close()
        
        if self.db:
            self.db.close()
        
        self.logger.info("监控已停止")
    
    def get_stats(self) -> dict:
        if self.db:
            return self.db.get_stats()
        return {}
    
    def get_dynamics(self, uid: str = None, limit: int = 50, offset: int = 0) -> List[dict]:
        if self.db:
            return self.db.get_dynamics(uid, limit, offset)
        return []
    
    def get_cookie_status(self) -> dict:
        if not self.cookie_manager:
            return {'valid': False, 'message': '未配置Cookie'}
        
        status = self.cookie_manager.check_cookie_status()
        remaining_days = self.cookie_manager.get_remaining_days()
        
        return {
            'valid': status.is_valid,
            'username': status.username,
            'uid': status.uid,
            'check_time': status.check_time,
            'remaining_days': remaining_days,
            'message': status.message,
        }
