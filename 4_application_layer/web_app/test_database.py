#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据库连接和疾病数据
"""

from py2neo import Graph

print("开始连接Neo4j数据库...")
try:
    # 连接到Neo4j数据库
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))
    print("数据库连接成功！")
    
    # 查找包含"糖尿病"的疾病
    print("\n查找包含'糖尿病'的疾病...")
    result = graph.run('MATCH (d:疾病) WHERE d.name CONTAINS "糖尿病" RETURN d.name').data()
    diabetes_diseases = [record['d.name'] for record in result]
    print(f"找到 {len(diabetes_diseases)} 个包含'糖尿病'的疾病：")
    for disease in diabetes_diseases:
        print(f"- {disease}")
    
    # 查找包含"高"的疾病，看看是否有高血压
    print("\n查找包含'高'的疾病（前10个）...")
    result = graph.run('MATCH (d:疾病) WHERE d.name CONTAINS "高" RETURN d.name LIMIT 10').data()
    high_diseases = [record['d.name'] for record in result]
    print(f"找到 {len(high_diseases)} 个包含'高'的疾病：")
    for disease in high_diseases:
        print(f"- {disease}")
        
    # 查找所有疾病，看看总共有多少个
    print("\n查找所有疾病...")
    result = graph.run('MATCH (d:疾病) RETURN count(d) as count').data()
    total_count = result[0]['count'] if result else 0
    print(f"总共有 {total_count} 个疾病")
    
    # 随机查找10个疾病，看看数据示例
    print("\n随机查找10个疾病...")
    result = graph.run('MATCH (d:疾病) RETURN d.name LIMIT 10').data()
    random_diseases = [record['d.name'] for record in result]
    for disease in random_diseases:
        print(f"- {disease}")
        
except Exception as e:
    print(f"错误：{e}")
