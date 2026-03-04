# -*- coding: utf-8 -*-

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bili_monitor.api.bili_api import BiliAPI, BiliAPIError, PermissionDeniedError, CookieExpiredError
from bili_monitor.core.config import LoggerConfig
from bili_monitor.core.logger import setup_logger


def test_opus_detail():
    config = LoggerConfig(level='INFO', file='logs/test_opus.log')
    logger = setup_logger(config)
    api = BiliAPI(logger=logger)
    
    test_cases = [
        {
            'opus_id': '1175602015758188569',
            'desc': '公开Opus内容测试',
        },
    ]
    
    for case in test_cases:
        opus_id = case['opus_id']
        desc = case['desc']
        
        print(f"\n{'='*60}")
        print(f"测试: {desc}")
        print(f"Opus ID: {opus_id}")
        print('='*60)
        
        try:
            opus = api.get_opus_detail(opus_id)
            
            if opus:
                print(f"\n标题: {opus.title or '(无标题)'}")
                print(f"作者: {opus.author_name} (UID: {opus.author_uid})")
                print(f"发布时间: {opus.publish_time}")
                print(f"编辑时间: {opus.edit_time or '未编辑'}")
                print(f"\n内容:\n{opus.content[:500]}..." if len(opus.content) > 500 else f"\n内容:\n{opus.content}")
                print(f"\n段落数: {len(opus.paragraphs)}")
                print(f"图片数: {len(opus.images)}")
                if opus.images:
                    print("图片列表:")
                    for i, img in enumerate(opus.images[:3]):
                        print(f"  {i+1}. {img.url[:60]}... ({img.width}x{img.height})")
                    if len(opus.images) > 3:
                        print(f"  ... 还有 {len(opus.images) - 3} 张图片")
                print(f"\n互动数据:")
                print(f"  点赞: {opus.stat.like}")
                print(f"  评论: {opus.stat.comment}")
                print(f"  转发: {opus.stat.repost}")
                print(f"\n测试成功!")
            else:
                print(f"未获取到 Opus 详情")
                
        except PermissionDeniedError as e:
            print(f"权限错误: {e}")
            print("可能原因: 内容需要登录或特定权限")
        except CookieExpiredError as e:
            print(f"Cookie错误: {e}")
            print("可能原因: 需要提供有效的Cookie")
        except BiliAPIError as e:
            print(f"API错误: {e} (code: {e.code})")
        except Exception as e:
            print(f"未知错误: {e}")
            import traceback
            traceback.print_exc()
    
    api.close()
    print("\n测试完成!")


if __name__ == '__main__':
    test_opus_detail()
