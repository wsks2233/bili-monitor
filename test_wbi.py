# -*- coding: utf-8 -*-
import logging
from bili_monitor.api.bili_api import BiliAPI

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test')

api = BiliAPI(logger)

print('=' * 60)
print('测试1: 获取WBI密钥')
print('=' * 60)
img_key, sub_key = api._get_wbi_keys()
print(f'img_key: {img_key}')
print(f'sub_key: {sub_key}')

print()
print('=' * 60)
print('测试2: 获取用户动态（带WBI签名）')
print('=' * 60)
dynamics = api.get_user_dynamics('1039025435', limit=3)
print(f'获取到 {len(dynamics)} 条动态')
for dyn in dynamics[:3]:
    content_preview = dyn.content[:50] + '...' if dyn.content and len(dyn.content) > 50 else dyn.content
    print(f'  - [{dyn.dynamic_type}] {content_preview}')

api.close()
print()
print('=' * 60)
print('测试完成!')
print('=' * 60)
