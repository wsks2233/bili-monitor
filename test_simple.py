# -*- coding: utf-8 -*-
import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://space.bilibili.com/1039025435/dynamic',
}

url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
params = {
    'offset': '',
    'host_mid': '1039025435',
    'timezone_offset': '-480',
    'platform': 'web',
    'features': 'itemOpusStyle,listOnlyfans,opusBigCover,onlyfansVote,forwardListHidden,decorationCard,commentsNewVersion,onlyfansAssetsV2,ugcDelete,onlyfansQaCard,avatarAutoTheme,sunflowerStyle,cardsEnhance,eva3CardOpus,eva3CardVideo,eva3CardComment,eva3CardUser',
    'web_location': '333.1387',
}

print('=' * 60)
print('测试简单请求（无Cookie）')
print('=' * 60)

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f'状态码: {resp.status_code}')
print(f'响应头: {dict(resp.headers)}')

data = resp.json()
print(f'\ncode: {data.get("code")}')
print(f'message: {data.get("message")}')

if data.get('code') == 0:
    items = data.get('data', {}).get('items', [])
    print(f'获取到 {len(items)} 条动态')
else:
    print(f'错误响应: {json.dumps(data, ensure_ascii=False)[:500]}')
