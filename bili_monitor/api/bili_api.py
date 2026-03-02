# -*- coding: utf-8 -*-

import logging
import os
import json
import time
import hashlib
import urllib.parse
import random
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.models import DynamicInfo, UpstreamInfo, StatInfo, VideoInfo, ImageInfo


class BiliAPIError(Exception):
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class RateLimitError(BiliAPIError):
    pass


class BiliAPI:
    DYNAMIC_SPACE_API = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
    DYNAMIC_DETAIL_API = "https://api.bilibili.com/x/polymer/web-dynamic/v1/detail"
    DYNAMIC_SPACE_API_OLD = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history"
    USER_INFO_API = "https://api.bilibili.com/x/space/wbi/acc/info"
    USER_STAT_API = "https://api.bilibili.com/x/relation/stat"
    NAV_API = "https://api.bilibili.com/x/web-interface/nav"
    WBI_KEYS_API = "https://api.bilibili.com/x/web-interface/nav"
    
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
        33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
        61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
        36, 20, 34, 44, 52
    ]
    
    # 随机间隔配置（秒）
    INTERVAL_CONFIG = {
        'min_interval': 1.5,        # 最小基础间隔
        'max_interval': 3.0,        # 最大基础间隔
        'retry_base': 5.0,          # 重试基础等待时间
        'retry_jitter': 3.0,        # 重试随机抖动范围
        'image_download': (0.5, 1.5),  # 图片下载间隔
        'detail_fetch': (0.8, 2.0),    # 详情获取间隔
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None, cookie: str = ""):
        self.logger = logger or logging.getLogger('bili-monitor')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://space.bilibili.com',
        })
        if cookie:
            self.session.headers['Cookie'] = cookie
            self.logger.info("已设置Cookie认证")
        
        self._wbi_keys = None
        self._last_request_time = 0
        self._user_cache: Dict[str, UpstreamInfo] = {}
    
    def _random_sleep(self, min_sec: float = None, max_sec: float = None):
        """随机等待，模拟人类行为"""
        if min_sec is None:
            min_sec = self.INTERVAL_CONFIG['min_interval']
        if max_sec is None:
            max_sec = self.INTERVAL_CONFIG['max_interval']
        
        wait_time = random.uniform(min_sec, max_sec)
        self.logger.debug(f"等待 {wait_time:.2f} 秒")
        time.sleep(wait_time)
    
    def _wait_for_rate_limit(self):
        """等待以避免触发频率限制（带随机性）"""
        elapsed = time.time() - self._last_request_time
        min_interval = random.uniform(
            self.INTERVAL_CONFIG['min_interval'],
            self.INTERVAL_CONFIG['max_interval']
        )
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed + random.uniform(0.2, 0.8)
            time.sleep(wait_time)
        self._last_request_time = time.time()
    
    def _get_wbi_keys(self) -> tuple:
        if self._wbi_keys:
            return self._wbi_keys
        
        self._wait_for_rate_limit()
        
        try:
            resp = self.session.get(self.WBI_KEYS_API, timeout=30)
            data = resp.json()
            
            if data.get('code') == 0:
                wbi_img = data.get('data', {}).get('wbi_img', {})
                img_key = wbi_img.get('img_url', '').split('/')[-1].split('.')[0]
                sub_key = wbi_img.get('sub_url', '').split('/')[-1].split('.')[0]
                
                self._wbi_keys = (img_key, sub_key)
                return self._wbi_keys
        except Exception as e:
            self.logger.error(f"获取WBI密钥失败: {e}")
        
        return None, None
    
    def _get_mixin_key(self, orig: str) -> str:
        return ''.join([orig[i] for i in self.MIXIN_KEY_ENC_TAB])[:32]
    
    def _sign_wbi(self, params: dict) -> dict:
        img_key, sub_key = self._get_wbi_keys()
        
        if not img_key or not sub_key:
            return params
        
        mixin_key = self._get_mixin_key(img_key + sub_key)
        
        wts = int(time.time())
        params['wts'] = wts
        
        params = dict(sorted(params.items()))
        
        query = urllib.parse.urlencode(params)
        query = query.replace('!', '%21').replace("'", '%27').replace('(', '%28').replace(')', '%29').replace('*', '%2A')
        
        w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
        params['w_rid'] = w_rid
        
        return params
    
    def _request(self, url: str, params: Dict[str, Any] = None, max_retries: int = 3) -> Dict[str, Any]:
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                code = data.get('code', 0)
                
                # 频率限制错误
                if code == -799:
                    wait_time = (attempt + 1) * self.INTERVAL_CONFIG['retry_base'] + random.uniform(1, self.INTERVAL_CONFIG['retry_jitter'])
                    self.logger.warning(f"触发频率限制，等待 {wait_time:.1f} 秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                if code != 0:
                    error_msg = data.get('message', 'Unknown error')
                    self.logger.error(f"API错误 [{code}]: {error_msg}, URL: {url}")
                    raise BiliAPIError(f"API返回错误 [{code}]: {error_msg}", code)
                
                return data
                
            except requests.RequestException as e:
                self.logger.error(f"请求失败: {e}, URL: {url}")
                if attempt < max_retries - 1:
                    self._random_sleep(2, 4)
                    continue
                raise
        
        raise BiliAPIError("请求失败，超过最大重试次数")
    
    def get_user_dynamics(self, uid: str, offset: str = "", limit: int = 20) -> List[DynamicInfo]:
        self.logger.info(f"获取用户 {uid} 的动态列表")
        
        dynamics = []
        
        self.session.headers['Referer'] = f'https://space.bilibili.com/{uid}/dynamic'
        
        # 使用完整参数的新版API
        params = {
            'offset': offset,
            'host_mid': uid,
            'timezone_offset': '-480',
            'platform': 'web',
            'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,avatarAutoTheme,sunflowerStyle,cardsEnhance,eva3CardOpus,eva3CardVideo,eva3CardComment,eva3CardUser',
            'web_location': '333.1387',
        }
        
        # 添加WBI签名
        signed_params = self._sign_wbi(params.copy())
        
        try:
            data = self._request(self.DYNAMIC_SPACE_API, signed_params)
            items = data.get('data', {}).get('items', []) or []
            
            self.logger.info(f"新版API返回 {len(items)} 条动态")
            
            for item in items[:limit]:
                try:
                    dynamic = self._parse_dynamic_new(item, uid)
                    if dynamic:
                        dynamics.append(dynamic)
                except Exception as e:
                    self.logger.error(f"解析动态失败: {e}")
                    
        except Exception as e:
            self.logger.warning(f"新版API失败: {e}")
            
            # 备用方案：使用老版API获取ID + 详情API
            self.logger.info("尝试备用方案...")
            dynamics = self._get_dynamics_fallback(uid, offset, limit)
        
        self.logger.info(f"获取用户 {uid} 动态 {len(dynamics)} 条")
        return dynamics
    
    def _get_dynamics_fallback(self, uid: str, offset: str, limit: int) -> List[DynamicInfo]:
        """备用方案：老版API获取ID + 详情API获取内容"""
        dynamics = []
        
        # 获取动态ID列表
        params = {
            'host_uid': uid,
            'offset_dynamic_id': offset or '0',
            'need_top': 0,
            'platform': 'web',
        }
        
        try:
            data = self._request(self.DYNAMIC_SPACE_API_OLD, params)
            cards = data.get('data', {}).get('cards', []) or []
            
            self.logger.info(f"老版API返回 {len(cards)} 条动态ID")
            
            for card in cards[:limit]:
                desc = card.get('desc', {})
                dyn_id = str(desc.get('dynamic_id_str', ''))
                if dyn_id:
                    try:
                        # 随机间隔
                        self._random_sleep(*self.INTERVAL_CONFIG['detail_fetch'])
                        dynamic = self.get_dynamic_detail(dyn_id)
                        if dynamic:
                            dynamic.uid = uid
                            dynamics.append(dynamic)
                    except Exception as e:
                        self.logger.error(f"获取动态详情失败 {dyn_id}: {e}")
                        
        except Exception as e:
            self.logger.error(f"备用方案失败: {e}")
        
        return dynamics
    
    def _parse_dynamic_new(self, item: Dict[str, Any], uid: str) -> Optional[DynamicInfo]:
        if not item:
            return None
        
        dynamic_id = str(item.get('id_str', ''))
        if not dynamic_id:
            return None
        
        dynamic_type = str(item.get('type', ''))
        type_name = self._get_dynamic_type_name(dynamic_type)
        
        # 检查是否是充电专属动态
        basic = item.get('basic', {})
        is_only_fans = basic.get('is_only_fans', False)
        
        modules = item.get('modules', {}) or {}
        
        author = modules.get('module_author', {}) or {}
        upstream_name = author.get('name', '')
        
        pub_ts = author.get('pub_ts', 0) or author.get('pub_time', 0)
        if isinstance(pub_ts, str):
            try:
                pub_ts = int(pub_ts)
            except:
                pub_ts = 0
        publish_time = datetime.fromtimestamp(pub_ts) if pub_ts else datetime.now()
        
        content = self._extract_content_new(modules)
        images = self._extract_images_new(modules)
        video = self._extract_video_new(modules)
        stat = self._extract_stat_new(modules)
        
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
    
    def _extract_content_new(self, modules: Dict[str, Any]) -> str:
        parts = []
        
        if not modules:
            return ''
        
        module_dynamic = modules.get('module_dynamic') or {}
        
        desc = module_dynamic.get('desc') or {}
        if isinstance(desc, dict):
            text = desc.get('text', '')
            if text:
                parts.append(text)
        
        major = module_dynamic.get('major') or {}
        
        # Opus类型动态（包括充电专属）
        opus = major.get('opus') or {}
        if opus:
            opus_title = opus.get('title', '')
            opus_summary = (opus.get('summary') or {}).get('text', '')
            if opus_title:
                parts.append(f"【标题】{opus_title}")
            if opus_summary:
                parts.append(opus_summary)
        
        archive = major.get('archive') or {}
        if archive:
            title = archive.get('title', '')
            desc_text = archive.get('desc', '')
            if title:
                parts.append(f"【视频】{title}")
            if desc_text:
                parts.append(desc_text)
        
        draw = major.get('draw') or {}
        if draw:
            desc_obj = draw.get('desc') or {}
            if isinstance(desc_obj, dict):
                draw_text = desc_obj.get('text', '')
                if draw_text:
                    parts.append(draw_text)
        
        return '\n'.join(parts)
    
    def _extract_images_new(self, modules: Dict[str, Any]) -> List[ImageInfo]:
        images = []
        
        if not modules:
            return images
        
        module_dynamic = modules.get('module_dynamic') or {}
        major = module_dynamic.get('major') or {}
        
        # Opus类型动态的图片
        opus = major.get('opus') or {}
        opus_pics = opus.get('pics') or []
        for pic in opus_pics:
            url = pic.get('url', '')
            if url:
                images.append(ImageInfo(
                    url=url,
                    width=pic.get('width', 0),
                    height=pic.get('height', 0),
                ))
        
        # Draw类型动态的图片
        draw = major.get('draw') or {}
        items = draw.get('items') or []
        for img in items:
            src = img.get('src', '')
            if src:
                images.append(ImageInfo(
                    url=src,
                    width=img.get('width', 0),
                    height=img.get('height', 0),
                ))
        
        return images
    
    def _extract_video_new(self, modules: Dict[str, Any]) -> Optional[VideoInfo]:
        if not modules:
            return None
        
        module_dynamic = modules.get('module_dynamic') or {}
        major = module_dynamic.get('major') or {}
        
        archive = major.get('archive') or {}
        if archive:
            return VideoInfo(
                bvid=archive.get('bvid', ''),
                aid=archive.get('aid', 0),
                title=archive.get('title', ''),
                description=archive.get('desc', ''),
                duration=0,
                cover=archive.get('cover', ''),
            )
        
        return None
    
    def _extract_stat_new(self, modules: Dict[str, Any]) -> StatInfo:
        stat = StatInfo()
        
        if not modules:
            return stat
        
        module_stat = modules.get('module_stat') or {}
        
        like = module_stat.get('like') or {}
        stat.like = like.get('count', 0) if isinstance(like, dict) else (like or 0)
        
        forward = module_stat.get('forward') or {}
        stat.repost = forward.get('count', 0) if isinstance(forward, dict) else (forward or 0)
        
        comment = module_stat.get('comment') or {}
        stat.comment = comment.get('count', 0) if isinstance(comment, dict) else (comment or 0)
        
        return stat
    
    def _get_dynamic_type_name(self, dynamic_type: str) -> str:
        type_map = {
            'DYNAMIC_TYPE_NONE': '无效动态',
            'DYNAMIC_TYPE_FORWARD': '转发',
            'DYNAMIC_TYPE_AV': '投稿视频',
            'DYNAMIC_TYPE_PGC': '番剧/影视',
            'DYNAMIC_TYPE_COURSES': '课程',
            'DYNAMIC_TYPE_WORD': '纯文字',
            'DYNAMIC_TYPE_DRAW': '图文',
            'DYNAMIC_TYPE_ARTICLE': '专栏文章',
            'DYNAMIC_TYPE_MUSIC': '音频',
            'DYNAMIC_TYPE_COMMON_SQUARE': '卡片',
            'DYNAMIC_TYPE_LIVE_RCMD': '直播推荐',
            'DYNAMIC_TYPE_MEDIALIST': '收藏夹',
            'DYNAMIC_TYPE_COURSES_SEASON': '课程系列',
            'DYNAMIC_TYPE_OPUS': '图文动态',
        }
        return type_map.get(dynamic_type, dynamic_type)
    
    def get_dynamic_detail(self, dynamic_id: str) -> Optional[DynamicInfo]:
        self.logger.debug(f"获取动态详情: {dynamic_id}")
        
        self.session.headers['Referer'] = f'https://www.bilibili.com/opus/{dynamic_id}'
        
        params = {'id': dynamic_id}
        
        try:
            data = self._request(self.DYNAMIC_DETAIL_API, params)
            item = data.get('data', {}).get('item', {})
            
            if item:
                return self._parse_dynamic_new(item, '')
        except Exception as e:
            self.logger.error(f"获取动态详情失败: {e}")
        
        return None
    
    def download_image(self, url: str, save_path: str) -> bool:
        # 随机等待
        self._random_sleep(*self.INTERVAL_CONFIG['image_download'])
        
        try:
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            headers = {'Referer': 'https://www.bilibili.com/'}
            response = self.session.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"图片下载成功: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"图片下载失败: {e}")
            return False
    
    def get_user_info(self, uid: str) -> Optional[UpstreamInfo]:
        # 检查缓存
        if uid in self._user_cache:
            self.logger.debug(f"使用缓存的用户信息: {uid}")
            return self._user_cache[uid]
        
        self.logger.debug(f"获取用户 {uid} 的信息")
        
        self.session.headers['Referer'] = f'https://space.bilibili.com/{uid}/'
        
        # 使用WBI签名
        params = self._sign_wbi({'mid': uid})
        
        try:
            data = self._request(self.USER_INFO_API, params)
            result = data.get('data', data)
            
            user_info = UpstreamInfo(
                uid=uid,
                name=result.get('name', ''),
                face=result.get('face', ''),
                sign=result.get('sign', ''),
                level=result.get('level', 0),
            )
            
            # 缓存用户信息
            self._user_cache[uid] = user_info
            return user_info
        except Exception as e:
            self.logger.warning(f"获取用户 {uid} 信息失败: {e}")
            # 返回默认信息
            return UpstreamInfo(uid=uid, name='')
    
    def get_user_fans(self, uid: str) -> int:
        self.logger.debug(f"获取用户 {uid} 的粉丝数")
        
        try:
            data = self._request(self.USER_STAT_API, {'vmid': uid})
            result = data.get('data', data)
            return result.get('follower', 0)
        except Exception as e:
            self.logger.warning(f"获取用户 {uid} 粉丝数失败: {e}")
            return 0
    
    def close(self):
        self.session.close()
