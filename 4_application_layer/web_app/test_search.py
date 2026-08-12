#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试搜索建议功能
"""

import requests

# 测试搜索功能
def test_search(keyword):
    url = f"http://localhost:9090/api/diseases/search?keyword={keyword}"
    try:
        response = requests.get(url)
        result = response.json()
        print(f"搜索关键词: '{keyword}'")
        print(f"成功: {result['success']}")
        print(f"结果数量: {len(result['data'])}")
        print("结果:")
        for item in result['data']:
            print(f"- {item}")
        print()
    except Exception as e:
        print(f"搜索失败: {e}")
        print()

# 测试不同关键词
print("=== 测试搜索建议功能 ===")
test_search("高")
test_search("糖")
test_search("肺")
test_search("心")
test_search("肝")
