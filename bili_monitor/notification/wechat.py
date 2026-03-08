# -*- coding: utf-8 -*-
"""
微信通知器

支持：
- 企业微信机器人
- 企业微信应用
- Server酱
- PushPlus
"""

import logging
from typing import Optional
import requests

from .base import NotificationBase, NotificationResult
from ..core.models import DynamicInfo


class WeChatNotifier(NotificationBase):
    """微信通知器"""
    
    def __init__(
        self,
        webhook_url: str = "",
        serverchan_key: str = "",
        pushplus_token: str = "",
        corpid: str = "",
        corpsecret: str = "",
        agentid: str = "",
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(logger)
        self.webhook_url = webhook_url
        self.serverchan_key = serverchan_key
        self.pushplus_token = pushplus_token
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid
    
    def send(self, dynamic: DynamicInfo) -> NotificationResult:
        if self.webhook_url:
            return self._send_enterprise_wechat(dynamic)
        elif self.corpid and self.corpsecret and self.agentid:
            return self._send_enterprise_wechat_app(dynamic)
        elif self.serverchan_key:
            return self._send_serverchan(dynamic)
        elif self.pushplus_token:
            return self._send_pushplus(dynamic)
        else:
            return NotificationResult(success=False, message="未配置微信通知参数")
    
    def _send_enterprise_wechat(self, dynamic: DynamicInfo) -> NotificationResult:
        """企业微信机器人通知"""
        try:
            # 根据动态类型生成正确的链接
            if dynamic.dynamic_type in ['图文', '转发', '充电专属-图文']:
                url = f"https://t.bilibili.com/{dynamic.dynamic_id}"
            else:
                url = f"https://www.bilibili.com/opus/{dynamic.dynamic_id}"
            
            # 构建文本消息内容
            content_lines = []
            content_lines.append(f"【{dynamic.upstream_name} 发布了新动态】")
            content_lines.append(f"类型: {dynamic.dynamic_type}")
            content_lines.append(f"时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}")
            if dynamic.content:
                content_preview = dynamic.content[:200]
                if len(dynamic.content) > 200:
                    content_preview += "..."
                content_lines.append(f"内容: {content_preview}")
            content_lines.append(f"链接: {url}")
            
            content = "\n".join(content_lines)
            
            # 构建消息数据
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            response = requests.post(self.webhook_url, json=data, timeout=10)
            result = response.json()
            if result.get('errcode') == 0:
                return NotificationResult(success=True, message="企业微信通知发送成功")
            else:
                return NotificationResult(success=False, message=f"企业微信通知发送失败: {result.get('errmsg')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"企业微信通知发送异常: {e}")
    
    def _send_serverchan(self, dynamic: DynamicInfo) -> NotificationResult:
        """Server酱通知"""
        try:
            url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
            data = {"title": f"【B站动态】{dynamic.upstream_name}", "desp": self.format_message(dynamic)}
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            if result.get('code') == 0:
                return NotificationResult(success=True, message="Server酱通知发送成功")
            else:
                return NotificationResult(success=False, message=f"Server酱通知发送失败: {result.get('message')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"Server酱通知发送异常: {e}")
    
    def _send_pushplus(self, dynamic: DynamicInfo) -> NotificationResult:
        """PushPlus通知"""
        try:
            url = "http://www.pushplus.plus/send"
            data = {"token": self.pushplus_token, "title": f"【B站动态】{dynamic.upstream_name}", "content": self.format_message(dynamic)}
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get('code') == 200:
                return NotificationResult(success=True, message="PushPlus通知发送成功")
            else:
                return NotificationResult(success=False, message=f"PushPlus通知发送失败: {result.get('msg')}")
        except Exception as e:
            return NotificationResult(success=False, message=f"PushPlus通知发送异常: {e}")
    
    def _upload_image_to_wechat(self, image_url: str, access_token: str) -> Optional[str]:
        """上传图片到企业微信临时素材"""
        try:
            # 下载图片
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_data = response.content
            
            # 上传到企业微信
            upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image"
            files = {
                'media': ('image.jpg', image_data, 'image/jpeg')
            }
            upload_response = requests.post(upload_url, files=files, timeout=10)
            upload_result = upload_response.json()
            
            if upload_result.get('errcode', 0) == 0:
                return upload_result.get('media_id')
            else:
                self.logger.error(f"上传图片失败: {upload_result.get('errmsg')}")
                return None
        except Exception as e:
            self.logger.error(f"上传图片异常: {e}")
            return None
    
    def _build_message_content(self, dynamic: DynamicInfo, url: str) -> str:
        """构建消息内容"""
        content_lines = []
        content_lines.append(f"【{dynamic.upstream_name} 发布了新动态】")
        content_lines.append(f"类型: {dynamic.dynamic_type}")
        content_lines.append(f"时间: {dynamic.publish_time.strftime('%Y-%m-%d %H:%M')}")
        if dynamic.content:
            content_preview = dynamic.content[:200]
            if len(dynamic.content) > 200:
                content_preview += "..."
            content_lines.append(f"内容: {content_preview}")
        content_lines.append(f"点赞: {dynamic.stat.like:,} | 评论: {dynamic.stat.comment:,} | 转发: {dynamic.stat.repost:,}")
        content_lines.append(f"链接: {url}")
        return "\n".join(content_lines)
    
    def _send_text_message(self, send_url: str, content: str) -> NotificationResult:
        """发送文本消息"""
        data = {
            "touser": "@all",
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": content
            }
        }
        response = requests.post(send_url, json=data, timeout=10)
        result = response.json()
        if result.get('errcode') == 0:
            return NotificationResult(success=True, message="企业微信应用通知发送成功")
        else:
            return NotificationResult(success=False, message=f"企业微信应用通知发送失败: {result.get('errmsg')}")
    
    def _send_enterprise_wechat_app(self, dynamic: DynamicInfo) -> NotificationResult:
        """企业微信应用通知"""
        try:
            # 获取access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
            token_response = requests.get(token_url, timeout=10)
            token_result = token_response.json()
            if token_result.get('errcode') != 0:
                return NotificationResult(success=False, message=f"获取access_token失败: {token_result.get('errmsg')}")
            access_token = token_result.get('access_token')
            
            # 发送消息
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            # 根据动态类型生成正确的链接
            if dynamic.dynamic_type in ['图文', '转发', '充电专属-图文']:
                url = f"https://t.bilibili.com/{dynamic.dynamic_id}"
            else:
                url = f"https://www.bilibili.com/opus/{dynamic.dynamic_id}"
            
            # 如果有图片，先上传图片并发送图片消息
            if dynamic.images:
                # 发送前3张图片
                for i, image in enumerate(dynamic.images[:3]):
                    # 上传图片
                    media_id = self._upload_image_to_wechat(image.url, access_token)
                    
                    if media_id:
                        # 发送图片消息
                        data = {
                            "touser": "@all",
                            "msgtype": "image",
                            "agentid": self.agentid,
                            "image": {
                                "media_id": media_id
                            }
                        }
                        
                        response = requests.post(send_url, json=data, timeout=10)
                        result = response.json()
                        if result.get('errcode') != 0:
                            self.logger.warning(f"发送第{i+1}张图片失败: {result.get('errmsg')}")
            
            # 发送文本消息
            content = self._build_message_content(dynamic, url)
            return self._send_text_message(send_url, content)
        except Exception as e:
            return NotificationResult(success=False, message=f"企业微信应用通知发送异常: {e}")
    
    def test(self) -> bool:
        """测试通知器是否正常工作"""
        try:
            if self.webhook_url:
                data = {"msgtype": "text", "text": {"content": "B站动态监控测试消息"}}
                response = requests.post(self.webhook_url, json=data, timeout=10)
                return response.json().get('errcode') == 0
            elif self.corpid and self.corpsecret and self.agentid:
                # 获取access_token
                token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
                token_response = requests.get(token_url, timeout=10)
                token_result = token_response.json()
                if token_result.get('errcode') != 0:
                    return False
                access_token = token_result.get('access_token')
                
                # 发送测试消息
                send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
                articles = [{
                    "title": "B站动态监控测试消息",
                    "description": "这是一条测试消息，用于验证企业微信应用通知功能是否正常。",
                    "url": "https://www.bilibili.com",
                    "picurl": "https://i0.hdslb.com/bfs/face/member/noface.jpg"
                }]
                data = {
                    "touser": "@all",
                    "msgtype": "news",
                    "agentid": self.agentid,
                    "news": {
                        "articles": articles
                    }
                }
                response = requests.post(send_url, json=data, timeout=10)
                return response.json().get('errcode') == 0
            return False
        except Exception as e:
            self.logger.error(f"测试失败: {e}")
            return False
