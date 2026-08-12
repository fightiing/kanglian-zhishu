#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试肺炎咨询功能
"""

import requests
import json

API_BASE = "http://localhost:9090/api"

def test_single_consultation(disease_name, question):
    """测试单疾病咨询"""
    url = f"{API_BASE}/consultation/single"
    data = {
        "disease_name": disease_name,
        "question": question
    }
    
    print(f"\n=== 测试单疾病咨询 ===")
    print(f"疾病名称: {disease_name}")
    print(f"问题: {question}")
    
    try:
        # 增加超时时间到90秒
        response = requests.post(url, json=data, timeout=90)
        result = response.json()
        
        if result['success']:
            print(f"\n[成功] 咨询成功")
            print(f"回答:\n{result['data']['answer']}")
        else:
            print(f"\n[失败] 咨询失败: {result['message']}")
    except requests.exceptions.Timeout:
        print(f"\n[超时] 请求超时，但服务器可能仍在处理，请稍后查看结果")
    except Exception as e:
        print(f"\n[失败] 请求失败: {e}")

# 测试肺炎咨询
print("="*60)
print("肺炎咨询功能测试")
print("="*60)

test_single_consultation("肺炎", "肺炎患者需要注意什么？")
