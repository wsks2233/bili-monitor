# -*- coding: utf-8 -*-
import requests
import uuid
import time
import json

def generate_buvid():
    mac = uuid.uuid4().hex.upper()
    buvid = f"XY{mac}"
    return buvid

buvid3 = generate_buvid()
buvid4 = f"{generate_buvid()}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://space.bilibili.com',
    'Referer': 'https://space.bilibili.com/1039025435/dynamic',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}

cookies = {
    'buvid3': buvid3,
    'buvid4': buvid4,
    'CURRENT_FNVAL': '4048',
    'CURRENT_QUALITY': '80',
    'b_lsid': f"{generate_buvid()}",
    'enable_web_push': 'DISABLE',
    'header_theme_version': 'CLOSE',
    'home_feed_column': '4',
    'browser_resolution': '1920-1000',
}

print('=' * 60)
print('测试带buvid的请求')
print('=' * 60)
print(f'buvid3: {buvid3}')
print(f'buvid4: {buvid4}')

url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
params = {
    'offset': '',
    'host_mid': '1039025435',
    'timezone_offset': '-480',
    'platform': 'web',
}

resp = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=30)
print(f'\n状态码: {resp.status_code}')
data = resp.json()
print(f'code: {data.get("code")}')
print(f'message: {data.get("message")}')

if data.get('code') == 0:
    items = data.get('data', {}).get('items', [])
    print(f'获取到 {len(items)} 条动态')
    for item in items[:3]:
        print(f'  - {item.get("type")}: {item.get("modules", {}).get("module_author", {}).get("name", "")}')
else:
    print(f'错误响应: {json.dumps(data, ensure_ascii=False)[:500]}')
