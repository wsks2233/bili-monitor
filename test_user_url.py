# -*- coding: utf-8 -*-
import requests
import json

url = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?offset=&host_mid=1039025435&timezone_offset=-480&platform=web&features=itemOpusStyle%2ClistOnlyfans%2CopusBigCover%2ConlyfansVote%2CforwardListHidden%2CdecorationCard%2CcommentsNewVersion%2ConlyfansAssetsV2%2CugcDelete%2ConlyfansQaCard%2CavatarAutoTheme%2CsunflowerStyle%2CcardsEnhance%2Ceva3CardOpus%2Ceva3CardVideo%2Ceva3CardComment%2Ceva3CardUser&web_location=333.1387"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Origin': 'https://t.bilibili.com',
    'Referer': 'https://t.bilibili.com/',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}

print('=' * 60)
print('测试用户提供的成功请求URL')
print('=' * 60)

resp = requests.get(url, headers=headers, timeout=30)
print(f'状态码: {resp.status_code}')

if resp.status_code == 200:
    data = resp.json()
    print(f'code: {data.get("code")}')
    print(f'message: {data.get("message")}')
    
    if data.get('code') == 0:
        items = data.get('data', {}).get('items', [])
        print(f'获取到 {len(items)} 条动态')
        for item in items[:3]:
            author = item.get('modules', {}).get('module_author', {})
            print(f'  - {author.get("name")}: {item.get("type")}')
    else:
        print(f'API错误: {json.dumps(data, ensure_ascii=False)[:500]}')
else:
    print(f'HTTP错误: {resp.text[:500]}')
