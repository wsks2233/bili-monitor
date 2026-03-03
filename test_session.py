# -*- coding: utf-8 -*-
import requests
import json
import time

session = requests.Session()

session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.bilibili.com/',
})

print('=' * 60)
print('步骤1: 先访问B站首页获取Cookie')
print('=' * 60)
resp = session.get('https://www.bilibili.com/', timeout=30)
print(f'首页状态码: {resp.status_code}')
print(f'获取到的Cookie: {dict(session.cookies)}')

time.sleep(2)

print()
print('=' * 60)
print('步骤2: 访问nav接口')
print('=' * 60)
resp = session.get('https://api.bilibili.com/x/web-interface/nav', timeout=30)
data = resp.json()
print(f'code: {data.get("code")}')
print(f'message: {data.get("message")}')

wbi_img = data.get('data', {}).get('wbi_img', {})
if wbi_img:
    img_key = wbi_img.get('img_url', '').split('/')[-1].split('.')[0]
    sub_key = wbi_img.get('sub_url', '').split('/')[-1].split('.')[0]
    print(f'img_key: {img_key}')
    print(f'sub_key: {sub_key}')

time.sleep(2)

print()
print('=' * 60)
print('步骤3: 访问动态接口')
print('=' * 60)

session.headers['Referer'] = 'https://space.bilibili.com/1039025435/dynamic'
url = 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space'
params = {
    'offset': '',
    'host_mid': '1039025435',
    'timezone_offset': '-480',
    'platform': 'web',
}

resp = session.get(url, params=params, timeout=30)
print(f'状态码: {resp.status_code}')
print(f'响应内容类型: {resp.headers.get("Content-Type")}')

if resp.status_code == 200:
    try:
        data = resp.json()
        print(f'code: {data.get("code")}')
        print(f'message: {data.get("message")}')
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            print(f'获取到 {len(items)} 条动态')
    except:
        print(f'响应文本: {resp.text[:500]}')
else:
    print(f'响应文本: {resp.text[:500]}')
