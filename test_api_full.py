# -*- coding: utf-8 -*-

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.api.bili_api import BiliAPI, BiliAPIError, CookieExpiredError, PermissionDeniedError
from bili_monitor.core.config import LoggerConfig
from bili_monitor.core.logger import setup_logger

COOKIE = """enable_web_push=DISABLE; rpdid=|(YYYYlm)u)0J'u~R|)Jlk|k; enable_feed_channel=ENABLE; DedeUserID=277972141; DedeUserID__ckMd5=a7d4c305bc913507; hit-dyn-v2=1; fingerprint=e69e87d9994b4d110950d8eb928f66e8; buvid_fp_plain=undefined; buvid_fp=e69e87d9994b4d110950d8eb928f66e8; header_theme_version=OPEN; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; LIVE_BUVID=AUTO8917546270119422; buvid4=BF3094F6-AAD7-6577-0CE9-36DA17E50CC686341-025030113-Q1eXASKP+yIocrDGb+m2Qw%3D%3D; CURRENT_QUALITY=120; home_feed_column=4; PVID=1; CURRENT_FNVAL=4048; buvid3=797D5410-D8BA-CBB5-AFCE-CD2AD8B7253F37360infoc; b_nut=1772410437; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI2Njk2MzgsImlhdCI6MTc3MjQxMDM3OCwicGx0IjotMX0.cqC-G6zXvKlwSP3TsfTJDlYc37mZQ5hbmB_OLhscpzo; bili_ticket_expires=1772669578; _uuid=10F3B47109-E4C7-D863-33D9-107A13F71D10AD00110infoc; SESSDATA=e123864a%2C1787987301%2Cfaee7%2A31CjAdhOVJFs_muBKUn0QJZlyOaJWe46gkQll59nIL-dg_19ueVr8u7ajKNpJPenMs0joSVmNhSHNxMXVNRHhTbkJGbkZrd3hpZFp1LURpWlUxOTVZLVNfYzhBNGhnX0lpaVN6R1NqeUJjS3c5dVZhVktGRzZoZ3FyYVM5SGVIMS1yZmF5SGR6WmZRIIEC; bili_jct=ab499b735c99da0fc9c58e859bfede5c; browser_resolution=1206-690; sid=5p4xnl0x; bp_t_offset_277972141=1175483629237698560; b_lsid=22179636_19CB65DA9B4"""


def test_all_apis():
    config = LoggerConfig(level='INFO', file='logs/test_api_full.log')
    logger = setup_logger(config)
    api = BiliAPI(logger=logger, cookie=COOKIE)
    
    test_results = []
    
    print("\n" + "=" * 70)
    print("B站 API 接口完整测试")
    print("=" * 70)
    
    # 测试1: 获取用户信息
    print("\n" + "-" * 50)
    print("测试1: 获取用户信息 (get_user_info)")
    print("-" * 50)
    try:
        test_uid = "277972141"
        user_info = api.get_user_info(test_uid)
        if user_info:
            print(f"  用户名: {user_info.name}")
            print(f"  等级: Lv{user_info.level}")
            print(f"  签名: {user_info.sign[:50]}..." if len(user_info.sign) > 50 else f"  签名: {user_info.sign}")
            print(f"  头像: {user_info.face}")
            test_results.append(("get_user_info", True, ""))
        else:
            print("  结果: 未获取到用户信息")
            test_results.append(("get_user_info", False, "返回数据为空"))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_user_info", False, str(e)))
    
    # 测试2: 获取用户粉丝数
    print("\n" + "-" * 50)
    print("测试2: 获取用户粉丝数 (get_user_fans)")
    print("-" * 50)
    try:
        fans = api.get_user_fans(test_uid)
        print(f"  粉丝数: {fans}")
        test_results.append(("get_user_fans", True, ""))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_user_fans", False, str(e)))
    
    # 测试3: 获取用户动态列表
    print("\n" + "-" * 50)
    print("测试3: 获取用户动态列表 (get_user_dynamics)")
    print("-" * 50)
    try:
        dynamics = api.get_user_dynamics(test_uid, limit=5)
        print(f"  获取到动态数量: {len(dynamics)}")
        if dynamics:
            for i, dyn in enumerate(dynamics[:3]):
                content_preview = dyn.content[:50] + "..." if len(dyn.content) > 50 else dyn.content
                print(f"  动态{i+1}: [{dyn.dynamic_type}] {content_preview}")
                print(f"         ID: {dyn.dynamic_id}, 点赞: {dyn.stat.like}")
        test_results.append(("get_user_dynamics", True, ""))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_user_dynamics", False, str(e)))
    
    # 测试4: 获取动态详情
    print("\n" + "-" * 50)
    print("测试4: 获取动态详情 (get_dynamic_detail)")
    print("-" * 50)
    try:
        test_dynamic_id = "1175602015758188569"
        detail = api.get_dynamic_detail(test_dynamic_id)
        if detail:
            print(f"  动态ID: {detail.dynamic_id}")
            print(f"  类型: {detail.dynamic_type}")
            print(f"  作者: {detail.upstream_name}")
            content_preview = detail.content[:80] + "..." if len(detail.content) > 80 else detail.content
            print(f"  内容: {content_preview}")
            print(f"  点赞: {detail.stat.like}, 评论: {detail.stat.comment}")
            test_results.append(("get_dynamic_detail", True, ""))
        else:
            print("  结果: 未获取到动态详情")
            test_results.append(("get_dynamic_detail", False, "返回数据为空"))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_dynamic_detail", False, str(e)))
    
    # 测试5: 获取Opus详情
    print("\n" + "-" * 50)
    print("测试5: 获取Opus详情 (get_opus_detail)")
    print("-" * 50)
    try:
        test_opus_id = "1175602015758188569"
        opus = api.get_opus_detail(test_opus_id)
        if opus:
            print(f"  Opus ID: {opus.opus_id}")
            print(f"  标题: {opus.title or '(无标题)'}")
            print(f"  作者: {opus.author_name} (UID: {opus.author_uid})")
            print(f"  发布时间: {opus.publish_time}")
            content_preview = opus.content[:80] + "..." if len(opus.content) > 80 else opus.content
            print(f"  内容: {content_preview}")
            print(f"  图片数: {len(opus.images)}")
            print(f"  点赞: {opus.stat.like}, 评论: {opus.stat.comment}")
            test_results.append(("get_opus_detail", True, ""))
        else:
            print("  结果: 未获取到Opus详情")
            test_results.append(("get_opus_detail", False, "返回数据为空"))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_opus_detail", False, str(e)))
    
    # 测试6: 使用自定义Cookie获取Opus详情
    print("\n" + "-" * 50)
    print("测试6: 使用自定义Cookie获取Opus详情")
    print("-" * 50)
    try:
        opus = api.get_opus_detail(test_opus_id, cookie=COOKIE)
        if opus:
            print(f"  Opus ID: {opus.opus_id}")
            print(f"  作者: {opus.author_name}")
            print(f"  内容长度: {len(opus.content)} 字符")
            test_results.append(("get_opus_detail_with_cookie", True, ""))
        else:
            print("  结果: 未获取到Opus详情")
            test_results.append(("get_opus_detail_with_cookie", False, "返回数据为空"))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_opus_detail_with_cookie", False, str(e)))
    
    # 测试7: 获取其他用户动态
    print("\n" + "-" * 50)
    print("测试7: 获取其他用户动态 (测试UP主)")
    print("-" * 50)
    try:
        other_uid = "1039025435"
        dynamics = api.get_user_dynamics(other_uid, limit=3)
        print(f"  获取到动态数量: {len(dynamics)}")
        if dynamics:
            for i, dyn in enumerate(dynamics[:2]):
                content_preview = dyn.content[:40] + "..." if len(dyn.content) > 40 else dyn.content
                print(f"  动态{i+1}: [{dyn.dynamic_type}] {content_preview}")
        test_results.append(("get_other_user_dynamics", True, ""))
    except Exception as e:
        print(f"  错误: {e}")
        test_results.append(("get_other_user_dynamics", False, str(e)))
    
    api.close()
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    for name, success, error in test_results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {name}: {status}")
        if not success and error:
            print(f"    错误信息: {error}")
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n总计: {success_count} 通过, {fail_count} 失败")
    print("=" * 70)


if __name__ == '__main__':
    test_all_apis()
