# -*- coding: utf-8 -*-
import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.bilibili.com/',
}

print('=' * 60)
print('测试 nav 接口返回内容')
print('=' * 60)

resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=headers, timeout=30)
data = resp.json()
print(f'code: {data.get("code")}')
print(f'message: {data.get("message")}')

if 'data' in data:
    print(f'data keys: {list(data["data"].keys())}')
    if 'wbi_img' in data['data']:
        wbi_img = data['data']['wbi_img']
        print(f'wbi_img: {json.dumps(wbi_img, indent=2)}')
        img_key = wbi_img.get('img_url', '').split('/')[-1].split('.')[0]
        sub_key = wbi_img.get('sub_url', '').split('/')[-1].split('.')[0]
        print(f'img_key: {img_key}')
        print(f'sub_key: {sub_key}')

print()
print('=' * 60)
print('完整响应:')
print('=' * 60)
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
