"""B站 API 端点封装

将 B站 API 调用封装为清晰的方法。
"""

from __future__ import annotations

import logging
import os
import random
import time
from datetime import datetime
from typing import Any

import requests

from .client import BiliHTTPClient, BiliAPIError, CookieExpiredError, UserNotFoundError


# 动态类型映射
DYNAMIC_TYPE_MAP = {
    "DYNAMIC_TYPE_NONE": "无效动态",
    "DYNAMIC_TYPE_FORWARD": "转发",
    "DYNAMIC_TYPE_AV": "投稿视频",
    "DYNAMIC_TYPE_PGC": "番剧/影视",
    "DYNAMIC_TYPE_COURSES": "课程",
    "DYNAMIC_TYPE_WORD": "纯文字",
    "DYNAMIC_TYPE_DRAW": "图文",
    "DYNAMIC_TYPE_ARTICLE": "专栏文章",
    "DYNAMIC_TYPE_MUSIC": "音频",
    "DYNAMIC_TYPE_COMMON_SQUARE": "卡片",
    "DYNAMIC_TYPE_LIVE_RCMD": "直播推荐",
    "DYNAMIC_TYPE_MEDIALIST": "收藏夹",
    "DYNAMIC_TYPE_COURSES_SEASON": "课程系列",
    "DYNAMIC_TYPE_OPUS": "图文动态",
}


# API URLs
class APIURL:
    DYNAMIC_SPACE = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    DYNAMIC_DETAIL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail"
    DYNAMIC_SPACE_OLD = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history"
    USER_INFO = "https://api.bilibili.com/x/space/wbi/acc/info"
    USER_INFO_SIMPLE = "https://api.bilibili.com/x/web-interface/card"
    USER_STAT = "https://api.bilibili.com/x/relation/stat"
    NAV = "https://api.bilibili.com/x/web-interface/nav"
    WBI_TICKET = "https://api.bilibili.com/bilibili.ticket.url?format=json"
    QRCODE_GENERATE = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    QRCODE_POLL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"


# 数据模型（简化版，用于 API 返回）
class StatInfo:
    """统计信息"""
    def __init__(self, like: int = 0, repost: int = 0, comment: int = 0) -> None:
        self.like = like
        self.repost = repost
        self.comment = comment

    def to_dict(self) -> dict[str, int]:
        return {"like": self.like, "repost": self.repost, "comment": self.comment}


class ImageInfo:
    """图片信息"""
    def __init__(self, url: str = "", width: int = 0, height: int = 0) -> None:
        self.url = url
        self.width = width
        self.height = height

    def to_dict(self) -> dict[str, Any]:
        return {"url": self.url, "width": self.width, "height": self.height}


class VideoInfo:
    """视频信息"""
    def __init__(
        self,
        bvid: str = "",
        aid: int = 0,
        title: str = "",
        description: str = "",
        duration: int = 0,
        cover: str = "",
    ) -> None:
        self.bvid = bvid
        self.aid = aid
        self.title = title
        self.description = description
        self.duration = duration
        self.cover = cover

    def to_dict(self) -> dict[str, Any]:
        return {
            "bvid": self.bvid,
            "aid": self.aid,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "cover": self.cover,
        }


class DynamicInfo:
    """动态信息"""
    def __init__(
        self,
        dynamic_id: str,
        uid: str,
        upstream_name: str = "",
        dynamic_type: str = "",
        content: str = "",
        publish_time: datetime | None = None,
        create_time: datetime | None = None,
        images: list[ImageInfo] | None = None,
        video: VideoInfo | None = None,
        stat: StatInfo | None = None,
        raw_json: dict[str, Any] | None = None,
    ) -> None:
        self.dynamic_id = dynamic_id
        self.uid = uid
        self.upstream_name = upstream_name
        self.dynamic_type = dynamic_type
        self.content = content
        self.publish_time = publish_time or datetime.now()
        self.create_time = create_time or datetime.now()
        self.images = images or []
        self.video = video
        self.stat = stat or StatInfo()
        self.raw_json = raw_json or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "dynamic_id": self.dynamic_id,
            "uid": self.uid,
            "upstream_name": self.upstream_name,
            "dynamic_type": self.dynamic_type,
            "content": self.content,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "images": [img.to_dict() for img in self.images],
            "video": self.video.to_dict() if self.video else None,
            "stat": self.stat.to_dict(),
        }


class UpstreamInfo:
    """UP主信息"""
    def __init__(
        self,
        uid: str,
        name: str = "",
        face: str = "",
        sign: str = "",
        level: int = 0,
        fans: int = 0,
    ) -> None:
        self.uid = uid
        self.name = name
        self.face = face
        self.sign = sign
        self.level = level
        self.fans = fans

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "name": self.name,
            "face": self.face,
            "sign": self.sign,
            "level": self.level,
            "fans": self.fans,
        }


class BiliEndpoints:
    """B站 API 端点
    
    使用示例：
        client = BiliHTTPClient(cookie="your_cookie")
        api = BiliEndpoints(client)
        
        # 获取用户动态
        dynamics = api.get_user_dynamics("12345")
        
        # 获取用户信息
        user = api.get_user_info("12345")
        
        client.close()
    """
    
    # 图片下载间隔配置
    IMAGE_DOWNLOAD_INTERVAL = (0.5, 1.5)
    
    def __init__(
        self,
        client: BiliHTTPClient,
        logger: logging.Logger | None = None,
    ) -> None:
        self._client = client
        self._logger = logger or logging.getLogger("bili-monitor.api")
        self._user_cache: dict[str, UpstreamInfo] = {}
    
    def _get_wbi_keys(self) -> tuple[str, str] | None:
        """获取 WBI 密钥"""
        if self._client.wbi.is_valid:
            return self._client.wbi._img_key, self._client.wbi._sub_key
        
        # 尝试从 nav 接口获取
        try:
            data = self._client.get(APIURL.NAV)
            wbi_img = data.get("data", {}).get("wbi_img", {})
            if wbi_img:
                img_key = wbi_img.get("img_url", "").split("/")[-1].split(".")[0]
                sub_key = wbi_img.get("sub_url", "").split("/")[-1].split(".")[0]
                
                if img_key and sub_key:
                    self._client.wbi.update_keys(img_key, sub_key)
                    self._logger.debug(f"从 nav 接口获取 WBI 密钥成功")
                    return img_key, sub_key
        except Exception as e:
            self._logger.warning(f"从 nav 接口获取 WBI 密钥失败: {e}")
        
        # 尝试从 ticket 接口获取
        try:
            data = self._client.get(APIURL.WBI_TICKET)
            if data.get("code") == 0:
                nav_data = data.get("data", {}).get("nav", {})
                img_url = nav_data.get("img", "")
                sub_url = nav_data.get("sub", "")
                
                img_key = img_url.split("/")[-1].split(".")[0] if img_url else ""
                sub_key = sub_url.split("/")[-1].split(".")[0] if sub_url else ""
                
                if img_key and sub_key:
                    self._client.wbi.update_keys(img_key, sub_key)
                    self._logger.debug(f"从 ticket 接口获取 WBI 密钥成功")
                    return img_key, sub_key
        except Exception as e:
            self._logger.warning(f"从 ticket 接口获取 WBI 密钥失败: {e}")
        
        self._logger.error("获取 WBI 密钥失败")
        return None
    
    def get_user_dynamics(
        self,
        uid: str,
        offset: str = "",
        limit: int = 20,
    ) -> list[DynamicInfo]:
        """获取用户动态列表
        
        Args:
            uid: 用户 UID
            offset: 分页偏移
            limit: 返回数量限制
            
        Returns:
            动态列表
        """
        self._logger.info(f"获取用户 {uid} 的动态列表")
        
        dynamics: list[DynamicInfo] = []
        
        # 确保 WBI 密钥有效
        self._get_wbi_keys()
        
        params = {
            "offset": offset,
            "host_mid": uid,
            "timezone_offset": "-480",
            "platform": "web",
            "features": "itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,avatarAutoTheme,sunflowerStyle,cardsEnhance,eva3CardOpus,eva3CardVideo,eva3CardComment,eva3CardUser",
            "web_location": "333.1387",
        }
        
        try:
            data = self._client.get_signed(APIURL.DYNAMIC_SPACE, params)
            items = data.get("data", {}).get("items", []) or []
            
            self._logger.info(f"新版 API 返回 {len(items)} 条动态")
            
            for item in items[:limit]:
                try:
                    dynamic = self._parse_dynamic(item, uid)
                    if dynamic:
                        dynamics.append(dynamic)
                except Exception as e:
                    self._logger.error(f"解析动态失败: {e}")
                    
        except Exception as e:
            error_str = str(e)
            if "412" in error_str:
                self._logger.warning("请求被 B 站风控拦截(412)")
            else:
                self._logger.warning(f"新版 API 失败: {e}")
            
            dynamics = self._get_dynamics_fallback(uid, offset, limit)
        
        self._logger.info(f"获取用户 {uid} 动态 {len(dynamics)} 条")
        return dynamics
    
    def _get_dynamics_fallback(
        self,
        uid: str,
        offset: str,
        limit: int,
    ) -> list[DynamicInfo]:
        """备用方案：老版 API 获取 ID + 详情 API 获取内容"""
        dynamics: list[DynamicInfo] = []
        
        params = {
            "host_uid": uid,
            "offset_dynamic_id": offset or "0",
            "need_top": 0,
            "platform": "web",
        }
        
        try:
            data = self._client.get(APIURL.DYNAMIC_SPACE_OLD, params)
            cards = data.get("data", {}).get("cards", []) or []
            
            self._logger.info(f"老版 API 返回 {len(cards)} 条动态 ID")
            
            for card in cards[:limit]:
                desc = card.get("desc", {})
                dyn_id = str(desc.get("dynamic_id_str", ""))
                if dyn_id:
                    try:
                        time.sleep(random.uniform(0.8, 2.0))
                        dynamic = self.get_dynamic_detail(dyn_id)
                        if dynamic:
                            dynamic.uid = uid
                            dynamics.append(dynamic)
                    except Exception as e:
                        self._logger.error(f"获取动态详情失败 {dyn_id}: {e}")
                        
        except Exception as e:
            self._logger.error(f"备用方案失败: {e}")
        
        return dynamics
    
    def get_dynamic_detail(self, dynamic_id: str) -> DynamicInfo | None:
        """获取动态详情
        
        Args:
            dynamic_id: 动态 ID
            
        Returns:
            动态信息，如果不存在返回 None
        """
        self._logger.debug(f"获取动态详情: {dynamic_id}")
        
        params = {"id": dynamic_id}
        
        try:
            data = self._client.get(APIURL.DYNAMIC_DETAIL, params)
            item = data.get("data", {}).get("item", {})
            
            if item:
                modules = item.get("modules", {}) or {}
                author = modules.get("module_author", {}) or {}
                uid = str(author.get("mid", ""))
                return self._parse_dynamic(item, uid)
        except Exception as e:
            self._logger.error(f"获取动态详情失败: {e}")
        
        return None
    
    def get_user_info(self, uid: str) -> UpstreamInfo:
        """获取用户信息
        
        Args:
            uid: 用户 UID
            
        Returns:
            用户信息
        """
        if uid in self._user_cache:
            self._logger.debug(f"使用缓存的用户信息: {uid}")
            return self._user_cache[uid]
        
        self._logger.debug(f"获取用户 {uid} 的信息")
        
        # 尝试简单 API
        try:
            data = self._client.get(APIURL.USER_INFO_SIMPLE, {"mid": uid, "photo": "true"})
            result = data.get("data", {})
            card = result.get("card", {})
            
            if card:
                user_info = UpstreamInfo(
                    uid=uid,
                    name=card.get("name", ""),
                    face=card.get("face", ""),
                    sign=card.get("sign", ""),
                    level=card.get("level_info", {}).get("current_level", 0),
                )
                
                self._user_cache[uid] = user_info
                return user_info
        except Exception as e:
            self._logger.warning(f"简单 API 获取用户 {uid} 信息失败: {e}")
        
        # 尝试 WBI 签名 API
        try:
            self._get_wbi_keys()
            data = self._client.get_signed(APIURL.USER_INFO, {"mid": uid})
            result = data.get("data", data)
            
            user_info = UpstreamInfo(
                uid=uid,
                name=result.get("name", ""),
                face=result.get("face", ""),
                sign=result.get("sign", ""),
                level=result.get("level", 0),
            )
            
            self._user_cache[uid] = user_info
            return user_info
        except Exception as e:
            self._logger.warning(f"获取用户 {uid} 信息失败: {e}")
            return UpstreamInfo(uid=uid)
    
    def get_user_fans(self, uid: str) -> int:
        """获取用户粉丝数
        
        Args:
            uid: 用户 UID
            
        Returns:
            粉丝数
        """
        self._logger.debug(f"获取用户 {uid} 的粉丝数")
        
        try:
            data = self._client.get(APIURL.USER_STAT, {"vmid": uid})
            result = data.get("data", data)
            return result.get("follower", 0)
        except Exception as e:
            self._logger.warning(f"获取用户 {uid} 粉丝数失败: {e}")
            return 0
    
    def download_image(self, url: str, save_path: str) -> bool:
        """下载图片
        
        Args:
            url: 图片 URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        time.sleep(random.uniform(*self.IMAGE_DOWNLOAD_INTERVAL))
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 使用独立 session 下载图片
            download_session = requests.Session()
            
            # 针对 HDSLB CDN 的特殊处理
            if "hdslb.com" in url or "biliapi.net" in url:
                download_session.headers.update({
                    "Referer": "https://www.bilibili.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                })
            else:
                download_session.headers.update({
                    "Referer": "https://www.bilibili.com/",
                })
            
            try:
                response = download_session.get(url, timeout=60)
                response.raise_for_status()
                
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                self._logger.info(f"图片下载成功: {save_path}")
                return True
            finally:
                download_session.close()
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                self._logger.error(f"图片下载失败: 403 Forbidden - 可能是防盗链限制, URL: {url}")
            else:
                self._logger.error(f"图片下载失败: HTTP {e.response.status_code}, URL: {url}")
            return False
        except Exception as e:
            self._logger.error(f"图片下载失败: {e}, URL: {url}")
            return False
    
    def get_qrcode(self) -> tuple[str, str]:
        """获取登录二维码
        
        Returns:
            (qrcode_url, qrcode_key)
        """
        try:
            data = self._client.get(APIURL.QRCODE_GENERATE)
            
            if data.get("code") == 0:
                qrcode_url = data["data"].get("url", "")
                qrcode_key = data["data"].get("qrcode_key", "")
                if qrcode_url and qrcode_key:
                    return qrcode_url, qrcode_key
            
            raise BiliAPIError("获取二维码失败")
        except Exception as e:
            self._logger.error(f"获取二维码失败: {e}")
            raise
    
    def check_login(self, qrcode_key: str) -> dict[str, Any]:
        """检查登录状态
        
        Args:
            qrcode_key: 二维码密钥
            
        Returns:
            登录状态信息
        """
        try:
            data = self._client.get(APIURL.QRCODE_POLL, {"qrcode_key": qrcode_key})
            
            if data.get("code") != 0:
                return {"success": False, "message": data.get("message", "请求失败")}
            
            login_data = data.get("data", {})
            status_code = login_data.get("code", -1)
            
            if status_code == 0:
                # 登录成功，提取 Cookie
                cookie = self._extract_cookie()
                user_info = self._get_user_info_from_cookie(cookie)
                
                return {
                    "success": True,
                    "status": 0,
                    "message": "登录成功",
                    "cookie": cookie,
                    "username": user_info.get("username"),
                    "uid": user_info.get("uid"),
                }
            else:
                messages = {
                    86101: "未扫码",
                    86090: "已扫码待确认",
                    86038: "二维码已过期",
                }
                return {
                    "success": False,
                    "status": status_code,
                    "message": messages.get(status_code, f"未知状态: {status_code}"),
                }
        except Exception as e:
            self._logger.error(f"检查登录状态失败: {e}")
            return {"success": False, "status": -1, "message": str(e)}
    
    def _extract_cookie(self) -> str:
        """从 session 中提取 Cookie"""
        cookies = []
        for cookie in self._client.session.cookies:
            cookies.append(f"{cookie.name}={cookie.value}")
        return "; ".join(cookies)
    
    def _get_user_info_from_cookie(self, cookie: str) -> dict[str, Any]:
        """从 Cookie 获取用户信息"""
        try:
            temp_client = BiliHTTPClient(cookie=cookie, logger=self._logger)
            try:
                data = temp_client.get(APIURL.NAV)
                if data.get("code") == 0:
                    user_data = data.get("data", {})
                    return {
                        "username": user_data.get("uname", ""),
                        "uid": user_data.get("mid", 0),
                    }
            finally:
                temp_client.close()
        except Exception as e:
            self._logger.error(f"获取用户信息失败: {e}")
        return {}
    
    def _parse_dynamic(self, item: dict[str, Any], uid: str) -> DynamicInfo | None:
        """解析动态数据"""
        if not item:
            return None
        
        dynamic_id = str(item.get("id_str", ""))
        if not dynamic_id:
            return None
        
        dynamic_type = str(item.get("type", ""))
        type_name = DYNAMIC_TYPE_MAP.get(dynamic_type, dynamic_type)
        
        # 检查是否是充电专属动态
        basic = item.get("basic", {})
        is_only_fans = basic.get("is_only_fans", False)
        
        modules = item.get("modules", {}) or {}
        
        author = modules.get("module_author", {}) or {}
        upstream_name = author.get("name", "")
        
        pub_ts = author.get("pub_ts", 0) or author.get("pub_time", 0)
        if isinstance(pub_ts, str):
            try:
                pub_ts = int(pub_ts)
            except ValueError:
                pub_ts = 0
        publish_time = datetime.fromtimestamp(pub_ts) if pub_ts else datetime.now()
        
        content = self._extract_content(modules)
        images = self._extract_images(modules)
        video = self._extract_video(modules)
        stat = self._extract_stat(modules)
        
        if is_only_fans:
            type_name = f"充电专属-{type_name}"
        
        return DynamicInfo(
            dynamic_id=dynamic_id,
            uid=uid,
            upstream_name=upstream_name,
            dynamic_type=type_name,
            content=content,
            publish_time=publish_time,
            create_time=datetime.now(),
            images=images,
            video=video,
            stat=stat,
            raw_json=item,
        )
    
    def _extract_content(self, modules: dict[str, Any]) -> str:
        """提取动态内容"""
        parts: list[str] = []
        
        if not modules:
            return ""
        
        module_dynamic = modules.get("module_dynamic") or {}
        
        desc = module_dynamic.get("desc") or {}
        if isinstance(desc, dict):
            text = desc.get("text", "")
            if text:
                parts.append(text)
        
        major = module_dynamic.get("major") or {}
        
        # Opus 类型动态
        opus = major.get("opus") or {}
        if opus:
            opus_title = opus.get("title", "")
            opus_summary = (opus.get("summary") or {}).get("text", "")
            if opus_title:
                parts.append(f"【标题】{opus_title}")
            if opus_summary:
                parts.append(opus_summary)
        
        archive = major.get("archive") or {}
        if archive:
            title = archive.get("title", "")
            desc_text = archive.get("desc", "")
            if title:
                parts.append(f"【视频】{title}")
            if desc_text:
                parts.append(desc_text)
        
        draw = major.get("draw") or {}
        if draw:
            desc_obj = draw.get("desc") or {}
            if isinstance(desc_obj, dict):
                draw_text = desc_obj.get("text", "")
                if draw_text:
                    parts.append(draw_text)
        
        return "\n".join(parts)
    
    def _extract_images(self, modules: dict[str, Any]) -> list[ImageInfo]:
        """提取动态图片"""
        images: list[ImageInfo] = []
        
        if not modules:
            return images
        
        module_dynamic = modules.get("module_dynamic") or {}
        major = module_dynamic.get("major") or {}
        
        # Opus 类型动态的图片
        opus = major.get("opus") or {}
        opus_pics = opus.get("pics") or []
        for pic in opus_pics:
            url = pic.get("url", "")
            if url:
                images.append(ImageInfo(
                    url=url,
                    width=pic.get("width", 0),
                    height=pic.get("height", 0),
                ))
        
        # Draw 类型动态的图片
        draw = major.get("draw") or {}
        items = draw.get("items") or []
        for img in items:
            src = img.get("src", "")
            if src:
                images.append(ImageInfo(
                    url=src,
                    width=img.get("width", 0),
                    height=img.get("height", 0),
                ))
        
        return images
    
    def _extract_video(self, modules: dict[str, Any]) -> VideoInfo | None:
        """提取动态视频"""
        if not modules:
            return None
        
        module_dynamic = modules.get("module_dynamic") or {}
        major = module_dynamic.get("major") or {}
        
        archive = major.get("archive") or {}
        if archive:
            return VideoInfo(
                bvid=archive.get("bvid", ""),
                aid=archive.get("aid", 0),
                title=archive.get("title", ""),
                description=archive.get("desc", ""),
                duration=0,
                cover=archive.get("cover", ""),
            )
        
        return None
    
    def _extract_stat(self, modules: dict[str, Any]) -> StatInfo:
        """提取动态统计"""
        stat = StatInfo()
        
        if not modules:
            return stat
        
        module_stat = modules.get("module_stat") or {}
        
        like = module_stat.get("like") or {}
        stat.like = like.get("count", 0) if isinstance(like, dict) else (like or 0)
        
        forward = module_stat.get("forward") or {}
        stat.repost = forward.get("count", 0) if isinstance(forward, dict) else (forward or 0)
        
        comment = module_stat.get("comment") or {}
        stat.comment = comment.get("count", 0) if isinstance(comment, dict) else (comment or 0)
        
        return stat
