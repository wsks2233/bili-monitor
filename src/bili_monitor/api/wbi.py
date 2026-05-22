"""WBI 签名模块

B站 API 的 WBI 签名实现，独立于 HTTP 客户端。
"""

from __future__ import annotations

import hashlib
import time
import urllib.parse
from typing import Any

# WBI 混淆表
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


class WBISigner:
    """WBI 签名器
    
    使用示例：
        signer = WBISigner()
        signer.update_keys("img_key", "sub_key")
        signed_params = signer.sign({"mid": "12345"})
    """
    
    def __init__(self) -> None:
        self._img_key: str = ""
        self._sub_key: str = ""
        self._update_time: float = 0
        # WBI 密钥有效期（秒），超过此时间需要刷新
        self._ttl: float = 3600  # 1 小时
    
    @property
    def is_valid(self) -> bool:
        """密钥是否有效"""
        if not self._img_key or not self._sub_key:
            return False
        return (time.time() - self._update_time) < self._ttl
    
    def update_keys(self, img_key: str, sub_key: str) -> None:
        """更新 WBI 密钥
        
        Args:
            img_key: 图片密钥
            sub_key: 子密钥
        """
        self._img_key = img_key
        self._sub_key = sub_key
        self._update_time = time.time()
    
    def get_mixin_key(self, orig: str) -> str:
        """获取混淆密钥"""
        return "".join([orig[i] for i in MIXIN_KEY_ENC_TAB])[:32]
    
    def sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """对参数进行 WBI 签名
        
        Args:
            params: 原始参数
            
        Returns:
            签名后的参数（包含 wts 和 w_rid）
        """
        if not self.is_valid:
            return params
        
        mixin_key = self.get_mixin_key(self._img_key + self._sub_key)
        
        # 添加时间戳
        wts = int(time.time())
        params["wts"] = wts
        
        # 按 key 排序
        params = dict(sorted(params.items()))
        
        # URL 编码
        query = urllib.parse.urlencode(params)
        # 替换特殊字符
        query = (
            query
            .replace("!", "%21")
            .replace("'", "%27")
            .replace("(", "%28")
            .replace(")", "%29")
            .replace("*", "%2A")
        )
        
        # 计算签名
        w_rid = hashlib.md5((query + mixin_key).encode()).hexdigest()
        params["w_rid"] = w_rid
        
        return params
