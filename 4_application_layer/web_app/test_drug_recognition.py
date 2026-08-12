#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试药品识别功能
"""

import requests
import json

API_BASE = "http://localhost:9090/api"

def test_drug_recognition():
    """测试药品识别功能"""
    url = f"{API_BASE}/drug/recognize"
    
    print("=== 测试药品识别功能 ===")
    
    try:
        # 由于没有实际的图片文件，我们使用一个简单的请求来测试接口
        # 注意：实际使用时需要上传图片文件
        # 这里我们只是测试接口是否能正常响应
        response = requests.post(url, files={
            'file': ('test.png', b'fake image data', 'image/png')
        }, timeout=30)
        
        result = response.json()
        
        if result['success']:
            print(f"[成功] 药品识别成功")
            print(f"消息: {result['message']}")
            print(f"药品名称: {result['data']['name']}")
            print(f"是否使用LLM: {result['data']['llm_used']}")
            print(f"结构化文本: {json.dumps(result['data']['structured_text'], ensure_ascii=False, indent=2)[:200]}...")
        else:
            print(f"[失败] 药品识别失败: {result['message']}")
    except Exception as e:
        print(f"[失败] 请求失败: {e}")

# 测试药品识别功能
print("="*60)
print("药品识别功能测试")
print("="*60)

test_drug_recognition()
