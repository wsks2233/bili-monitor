"""图片下载器"""

from __future__ import annotations

import logging
import os
import random
import time
from pathlib import Path

import requests


class ImageDownloader:
    """图片下载器
    
    使用示例：
        downloader = ImageDownloader(base_dir="images")
        downloader.download(url, "upstream_name", "dynamic_id", 0)
    """
    
    # 下载间隔配置
    DOWNLOAD_INTERVAL = (0.5, 1.5)
    
    def __init__(
        self,
        base_dir: str = "images",
        logger: logging.Logger | None = None,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._logger = logger or logging.getLogger("bili-monitor.image")
    
    def download(
        self,
        url: str,
        upstream_name: str,
        dynamic_id: str,
        index: int,
    ) -> str | None:
        """下载图片
        
        Args:
            url: 图片 URL
            upstream_name: UP主名称
            dynamic_id: 动态 ID
            index: 图片索引
            
        Returns:
            本地路径，如果下载失败返回 None
        """
        # 随机等待
        time.sleep(random.uniform(*self.DOWNLOAD_INTERVAL))
        
        # 生成安全的目录名
        safe_name = "".join(
            c for c in upstream_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_name:
            safe_name = dynamic_id.split("_")[0] if "_" in dynamic_id else dynamic_id
        
        # 生成文件名
        ext = ".jpg"
        if "?" in url:
            base_url = url.split("?")[0]
            if "." in base_url:
                ext = "." + base_url.rsplit(".", 1)[-1]
        
        filename = f"{index + 1:03d}{ext}"
        save_dir = self._base_dir / safe_name / dynamic_id
        save_path = save_dir / filename
        
        # 检查是否已存在
        if save_path.exists():
            self._logger.debug(f"图片已存在: {save_path}")
            return str(save_path)
        
        # 下载图片
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            
            session = requests.Session()
            
            # 针对 HDSLB CDN 的特殊处理
            if "hdslb.com" in url or "biliapi.net" in url:
                session.headers.update({
                    "Referer": "https://www.bilibili.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                })
            else:
                session.headers.update({
                    "Referer": "https://www.bilibili.com/",
                })
            
            try:
                response = session.get(url, timeout=60)
                response.raise_for_status()
                
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                self._logger.info(f"图片下载成功: {save_path}")
                return str(save_path)
            finally:
                session.close()
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                self._logger.error(f"图片下载失败: 403 Forbidden - 可能是防盗链限制, URL: {url}")
            else:
                self._logger.error(f"图片下载失败: HTTP {e.response.status_code}, URL: {url}")
            return None
        except Exception as e:
            self._logger.error(f"图片下载失败: {e}, URL: {url}")
            return None
