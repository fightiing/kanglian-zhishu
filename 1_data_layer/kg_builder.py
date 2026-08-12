#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
数据层 - 医疗知识图谱构建
================================================================================
职责：从medical.json加载数据，构建Neo4j知识图谱
功能：
  1. 加载医疗数据（疾病、症状、药物、食物等）
  2. 构建知识图谱节点和关系
  3. 提供统计信息

技术栈：py2neo + Neo4j
数据源：medical.json（500+疾病信息）
================================================================================
"""

import json
import sys
import os
from py2neo import Graph, Node, Relationship

class MedicalKGBuilder:
    """医疗知识图谱构建器"""

    def __init__(self, neo4j_uri=None, auth=None):
        """
        初始化Neo4j连接（支持本地与云端Neo4j AuraDB）
        优先级：显式参数 > 环境变量 > 本地默认值
        Args:
            neo4j_uri: Neo4j连接串，如 bolt://localhost:7687 或 neo4j+s://xxx.databases.neo4j.io
            auth: (用户名, 密码) 元组
        """
        try:
            # 1. 取参数 > 环境变量 > 默认本地
            if neo4j_uri is None:
                neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            if auth is None:
                user = os.getenv("NEO4J_USERNAME", "neo4j")
                pwd = os.getenv("NEO4J_PASSWORD", "12345678")
                auth = (user, pwd)

            # Neo4j AuraDB 需要 secure=True 兼容（py2neo 对 neo4j+s:// 自动识别）
            self.graph = Graph(neo4j_uri, auth=auth)
            # 探测连接
            self.graph.run("RETURN 1").data()
            print(f"+ Neo4j数据库连接成功 ({neo4j_uri})")
        except Exception as e:
            print(f"- Neo4j数据库连接失败: {e}")
            if "neo4j.io" in (neo4j_uri or ""):
                print("请检查 AuraDB 实例是否已启动、用户名/密码是否正确、网络是否可访问外网")
            else:
                print("请确保本地Neo4j服务已启动")
            sys.exit(1)

    def load_medical_data(self, file_path, limit=500):
        """
        加载医疗数据
        Args:
            file_path: 数据文件路径
            limit: 加载数据条数限制
        Returns:
            医疗数据列表
        """
        data_list = []
        print(f"\n正在加载医疗数据（前{limit}条）...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    try:
                        data = json.loads(line.strip())
                        data_list.append(data)
                    except json.JSONDecodeError:
                        print(f"  警告: 第{i+1}行数据解析失败，跳过")
                        continue
            
            print(f"+ 成功加载 {len(data_list)} 条医疗数据")
            return data_list
            
        except FileNotFoundError:
            print(f"- 错误: 找不到数据文件 {file_path}")
            print("请确保medical.json文件在项目根目录下")
            sys.exit(1)
    
    def build_knowledge_graph(self, data_list):
        """
        构建知识图谱
        核心逻辑：
        1. 疾病节点：存储疾病基本信息（名称、描述、病因、治疗周期等）
        2. 症状节点：疾病的临床表现
        3. 药物节点：治疗药物（推荐药物、常用药物）
        4. 食物节点：饮食建议（宜吃、忌吃）
        5. 科室节点：就诊科室
        6. 检查项目节点：诊断所需检查
        
        关系定义：
        - 疾病-症状表现->症状
        - 疾病-推荐药物/常用药物->药物
        - 疾病-宜吃/忌吃->食物
        - 疾病-就诊科室->科室
        - 疾病-需要检查->检查项目
        """
        print(f"\n开始构建知识图谱，共 {len(data_list)} 条数据...")
        
        for idx, data in enumerate(data_list):
            if (idx + 1) % 100 == 0:
                print(f"  进度: {idx + 1}/{len(data_list)}")
            
            # 创建疾病节点（核心实体）
            disease_name = data.get('name', '')
            if not disease_name:
                continue
            
            # 疾病节点包含关键医疗信息
            disease_node = Node(
                "疾病",
                name=disease_name,
                desc=data.get('desc', ''),  # 疾病描述
                prevent=data.get('prevent', ''),  # 预防措施
                cause=data.get('cause', ''),  # 病因
                get_prob=data.get('get_prob', ''),  # 患病概率
                get_way=data.get('get_way', ''),  # 传播方式
                cure_lasttime=data.get('cure_lasttime', ''),  # 治疗周期
                cured_prob=data.get('cured_prob', ''),  # 治愈率
                cost_money=data.get('cost_money', '')  # 治疗费用
            )
            self.graph.merge(disease_node, "疾病", "name")
            
            # 创建症状节点及关系（用于症状匹配诊断）
            symptoms = data.get('symptom', [])
            for symptom in symptoms:
                symptom_node = Node("症状", name=symptom)
                self.graph.merge(symptom_node, "症状", "name")
                rel = Relationship(disease_node, "症状表现", symptom_node)
                self.graph.merge(rel)
            
            # 创建并发症节点及关系（用于风险提示）
            acompanies = data.get('acompany', [])
            for acompany in acompanies:
                acompany_node = Node("并发症", name=acompany)
                self.graph.merge(acompany_node, "并发症", "name")
                rel = Relationship(disease_node, "可能并发", acompany_node)
                self.graph.merge(rel)
            
            # 创建科室节点及关系（用于就诊引导）
            departments = data.get('cure_department', [])
            for dept in departments:
                dept_node = Node("科室", name=dept)
                self.graph.merge(dept_node, "科室", "name")
                rel = Relationship(disease_node, "就诊科室", dept_node)
                self.graph.merge(rel)
            
            # 创建治疗方式节点及关系
            cure_ways = data.get('cure_way', [])
            for cure_way in cure_ways:
                cure_way_node = Node("治疗方式", name=cure_way)
                self.graph.merge(cure_way_node, "治疗方式", "name")
                rel = Relationship(disease_node, "治疗方法", cure_way_node)
                self.graph.merge(rel)
            
            # 创建检查项目节点及关系（用于诊断建议）
            checks = data.get('check', [])
            for check in checks:
                check_node = Node("检查项目", name=check)
                self.graph.merge(check_node, "检查项目", "name")
                rel = Relationship(disease_node, "需要检查", check_node)
                self.graph.merge(rel)
            
            # 创建推荐药物节点及关系（核心：用药安全检索）
            drugs = data.get('recommand_drug', [])
            for drug in drugs:
                drug_node = Node("药物", name=drug, type="推荐药物")
                self.graph.merge(drug_node, "药物", "name")
                rel = Relationship(disease_node, "推荐药物", drug_node)
                self.graph.merge(rel)
            
            # 创建常用药物节点及关系（核心：用药安全检索）
            common_drugs = data.get('common_drug', [])
            for drug in common_drugs:
                drug_node = Node("药物", name=drug, type="常用药物")
                self.graph.merge(drug_node, "药物", "name")
                rel = Relationship(disease_node, "常用药物", drug_node)
                self.graph.merge(rel)
            
            # 创建宜吃食物节点及关系（用于饮食指导）
            do_eat = data.get('do_eat', [])
            for food in do_eat:
                food_node = Node("食物", name=food, type="宜吃")
                self.graph.merge(food_node, "食物", "name")
                rel = Relationship(disease_node, "宜吃", food_node)
                self.graph.merge(rel)
            
            # 创建忌吃食物节点及关系（核心：用于食物禁忌检测）
            not_eat = data.get('not_eat', [])
            for food in not_eat:
                food_node = Node("食物", name=food, type="忌吃")
                self.graph.merge(food_node, "食物", "name")
                rel = Relationship(disease_node, "忌吃", food_node)
                self.graph.merge(rel)
        
        print("+ 知识图谱构建完成！")
    
    def get_statistics(self):
        """获取知识图谱统计信息"""
        print("\n=== 知识图谱统计信息 ===")
        
        node_types = ["疾病", "症状", "并发症", "科室", "治疗方式", "检查项目", "药物", "食物"]
        total_nodes = 0
        
        for node_type in node_types:
            query = f"MATCH (n:{node_type}) RETURN count(n) as count"
            result = self.graph.run(query).data()
            count = result[0]['count'] if result else 0
            total_nodes += count
            print(f"  {node_type}节点: {count}")
        
        query = "MATCH ()-[r]->() RETURN count(r) as count"
        result = self.graph.run(query).data()
        rel_count = result[0]['count'] if result else 0
        
        print(f"\n  节点总数: {total_nodes}")
        print(f"  关系总数: {rel_count}")
        print("="*30)


def main():
    """主函数（支持本地 / 云端 Neo4j 导入）"""
    print("="*50)
    print("康联智枢——面向主动健康的知识驱动医疗智能协同网络")
    print("模块：医疗知识图谱构建")
    print("="*50)
    print("连接方式: 显式参数 > 环境变量 NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD > 本地默认")
    print()

    # 允许通过命令行传入数据文件路径与数据条数
    data_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "medical.json")
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    # 初始化知识图谱构建器（读取环境变量）
    builder = MedicalKGBuilder()

    # 加载医疗数据
    medical_data = builder.load_medical_data(data_file, limit=limit)

    # 构建知识图谱
    builder.build_knowledge_graph(medical_data)

    # 显示统计信息
    builder.get_statistics()

    print("\n✓ 知识图谱已成功构建到Neo4j数据库")
    if os.getenv("NEO4J_URI") and "neo4j.io" in os.environ["NEO4J_URI"]:
        print("  目标：云端 Neo4j AuraDB")
    else:
        print("  访问 http://localhost:7474 可视化查看")
    print("\n下一步：启动 Flask Web 服务进行查询")


if __name__ == "__main__":
    main()
