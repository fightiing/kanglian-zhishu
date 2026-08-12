#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试智能咨询功能
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

def test_disease_info(disease_name):
    """测试疾病信息查询"""
    url = f"{API_BASE}/disease/info?name={disease_name}"
    
    print(f"\n=== 测试疾病信息查询 ===")
    print(f"疾病名称: {disease_name}")
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result['success']:
            print(f"\n[成功] 查询成功")
            data = result['data']
            print(f"疾病描述: {data['desc'][:100]}..." if len(data['desc']) > 100 else f"疾病描述: {data['desc']}")
            print(f"症状: {', '.join(data['symptoms'][:5])}")
            print(f"推荐药物: {', '.join(data['drugs'].get('推荐药物', [])[:5])}")
        else:
            print(f"\n[失败] 查询失败: {result['message']}")
    except Exception as e:
        print(f"\n[失败] 请求失败: {e}")

# 测试不同疾病的咨询
print("="*60)
print("智能咨询功能测试")
print("="*60)

# 先测试疾病信息查询
test_disease_info("高血压")
test_disease_info("肺炎")

# 再测试智能咨询
test_single_consultation("高血压", "高血压患者在饮食上应该注意什么？")
