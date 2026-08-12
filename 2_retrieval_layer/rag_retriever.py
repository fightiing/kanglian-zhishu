#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医疗知识RAG检索模块
功能：基于用户查询从知识图谱中检索相关医疗知识
检索策略：关键词匹配 + 图关系遍历
支持两种模式：
  1. Neo4j 图数据库模式（优先，功能完整）
  2. JSON 文件回退模式（当 Neo4j 不可用时，从 medical.json 加载数据）
"""

import sys
import os
import json


class MedicalRAGRetriever:
    """医疗知识RAG检索器"""

    def __init__(self, neo4j_uri="bolt://localhost:7687", auth=('neo4j', '12345678')):
        """
        初始化检索器，优先尝试 Neo4j 连接，失败则回退到 JSON 模式
        Args:
            neo4j_uri: Neo4j数据库连接地址
            auth: 认证信息
        """
        self.graph = None
        self.connected = False
        self._disease_db = None
        self._mode = None

        # 先尝试 Neo4j
        try:
            from py2neo import Graph
            self.graph = Graph(neo4j_uri, auth=auth)
            self.graph.run('MATCH (n) RETURN count(n) LIMIT 1').data()
            self.connected = True
            self._mode = 'neo4j'
            print("OK Neo4j数据库连接成功")
        except Exception as e:
            print(f"WARNING Neo4j数据库连接失败: {e}")
            print("切换到JSON回退模式...")
            self.graph = None
            self.connected = False

        # Neo4j 不可用时回退到 JSON
        if not self.connected:
            self._init_json_fallback()

    def _init_json_fallback(self):
        """从 medical.json 加载疾病数据到内存"""
        json_path = self._find_medical_json()
        if not json_path:
            print("ERROR 找不到 medical.json，JSON回退模式初始化失败")
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('['):
                    data = json.loads(content)
                else:
                    data = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            data.append(json.loads(line))

            self._disease_db = data
            self._mode = 'json'
            self.connected = True  # JSON模式也算已连接，使API正常工作
            print(f"OK JSON回退模式初始化成功，共加载 {len(data)} 条疾病数据")
        except Exception as e:
            print(f"ERROR 加载 medical.json 失败: {e}")
            self._disease_db = []
            self._mode = 'json'
            self.connected = False

    def _find_medical_json(self):
        """查找 medical.json 文件路径"""
        candidates = [
            # 项目根目录
            os.path.join(os.path.dirname(__file__), '..', '..', 'medical.json'),
            os.path.join(os.path.dirname(__file__), '..', 'medical.json'),
            os.path.join(os.getcwd(), 'medical.json'),
        ]
        for path in candidates:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path
        return None

    def _search_disease_json(self, disease_name):
        """在 JSON 数据中搜索疾病（模糊匹配）"""
        if not self._disease_db:
            return None
        # 先精确匹配
        for item in self._disease_db:
            if item.get('name', '') == disease_name:
                return item
        # 再模糊匹配（包含）
        for item in self._disease_db:
            if disease_name in item.get('name', '') or item.get('name', '') in disease_name:
                return item
        return None

    def _search_disease_json_all(self, disease_name):
        """在 JSON 数据中搜索所有匹配的疾病"""
        if not self._disease_db:
            return []
        results = []
        for item in self._disease_db:
            if disease_name in item.get('name', '') or item.get('name', '') in disease_name:
                results.append(item)
        return results

    def retrieve_disease_info(self, disease_name):
        """检索疾病基本信息"""
        if self._mode == 'neo4j' and self.connected:
            query = """
            MATCH (d:疾病)
            WHERE d.name CONTAINS $disease_name
            RETURN d
            LIMIT 1
            """
            try:
                result = self.graph.run(query, disease_name=disease_name).data()
                if result:
                    return dict(result[0]['d'])
                return None
            except Exception as e:
                print(f"检索疾病信息时出错: {e}")
                return None
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return None
            # 转换为与 Neo4j 查询结果兼容的格式
            return {
                'name': disease.get('name', ''),
                'desc': disease.get('desc', ''),
                'category': disease.get('category', []),
                'prevent': disease.get('prevent', ''),
                'cause': disease.get('cause', ''),
            }

    def retrieve_symptoms(self, disease_name):
        """检索疾病症状"""
        if self._mode == 'neo4j' and self.connected:
            query = """
            MATCH (d:疾病)-[:症状表现]->(s:症状)
            WHERE d.name CONTAINS $disease_name
            RETURN s.name as symptom
            """
            try:
                result = self.graph.run(query, disease_name=disease_name).data()
                return [r['symptom'] for r in result]
            except Exception as e:
                print(f"检索症状时出错: {e}")
                return []
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return []
            return disease.get('symptom', [])

    def retrieve_drugs(self, disease_name):
        """检索疾病用药"""
        if self._mode == 'neo4j' and self.connected:
            query_recommend = """
            MATCH (d:疾病)-[:推荐药物]->(drug:药物)
            WHERE d.name CONTAINS $disease_name
            RETURN drug.name as drug_name
            """
            query_common = """
            MATCH (d:疾病)-[:常用药物]->(drug:药物)
            WHERE d.name CONTAINS $disease_name
            RETURN drug.name as drug_name
            """
            try:
                recommend_result = self.graph.run(query_recommend, disease_name=disease_name).data()
                common_result = self.graph.run(query_common, disease_name=disease_name).data()
                return {
                    "推荐药物": [r['drug_name'] for r in recommend_result],
                    "常用药物": [r['drug_name'] for r in common_result]
                }
            except Exception as e:
                print(f"检索药物时出错: {e}")
                return {"推荐药物": [], "常用药物": []}
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return {"推荐药物": [], "常用药物": []}
            return {
                "推荐药物": disease.get('recommand_drug', []),
                "常用药物": disease.get('common_drug', [])
            }

    def retrieve_food_advice(self, disease_name):
        """检索饮食建议"""
        if self._mode == 'neo4j' and self.connected:
            query_do_eat = """
            MATCH (d:疾病)-[:宜吃]->(f:食物)
            WHERE d.name CONTAINS $disease_name
            RETURN f.name as food_name
            """
            query_not_eat = """
            MATCH (d:疾病)-[:忌吃]->(f:食物)
            WHERE d.name CONTAINS $disease_name
            RETURN f.name as food_name
            """
            try:
                do_eat_result = self.graph.run(query_do_eat, disease_name=disease_name).data()
                not_eat_result = self.graph.run(query_not_eat, disease_name=disease_name).data()
                return {
                    "宜吃": [r['food_name'] for r in do_eat_result],
                    "忌吃": [r['food_name'] for r in not_eat_result]
                }
            except Exception as e:
                print(f"检索饮食建议时出错: {e}")
                return {"宜吃": [], "忌吃": []}
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return {"宜吃": [], "忌吃": []}
            return {
                "宜吃": disease.get('do_eat', []),
                "忌吃": disease.get('not_eat', [])
            }

    def retrieve_departments(self, disease_name):
        """检索就诊科室"""
        if self._mode == 'neo4j' and self.connected:
            query = """
            MATCH (d:疾病)-[:就诊科室]->(dept:科室)
            WHERE d.name CONTAINS $disease_name
            RETURN dept.name as department
            """
            try:
                result = self.graph.run(query, disease_name=disease_name).data()
                return [r['department'] for r in result]
            except Exception as e:
                print(f"检索科室时出错: {e}")
                return []
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return []
            return disease.get('cure_department', [])

    def retrieve_checks(self, disease_name):
        """检索诊断检查项目"""
        if self._mode == 'neo4j' and self.connected:
            query = """
            MATCH (d:疾病)-[:需要检查]->(c:检查项目)
            WHERE d.name CONTAINS $disease_name
            RETURN c.name as check_item
            """
            try:
                result = self.graph.run(query, disease_name=disease_name).data()
                return [r['check_item'] for r in result]
            except Exception as e:
                print(f"检索检查项目时出错: {e}")
                return []
        else:
            disease = self._search_disease_json(disease_name)
            if not disease:
                return []
            return disease.get('check', [])

    def retrieve_multi_disease_drug_conflict(self, disease_list):
        """检索多疾病用药冲突"""
        all_drugs = {}
        for disease in disease_list:
            drugs = self.retrieve_drugs(disease)
            all_drugs[disease] = drugs
        return all_drugs

    def check_food_conflict(self, disease_list):
        """检查多疾病饮食冲突"""
        all_food_advice = {}
        for disease in disease_list:
            food_advice = self.retrieve_food_advice(disease)
            all_food_advice[disease] = food_advice

        conflicts = []
        diseases = list(all_food_advice.keys())

        for i in range(len(diseases)):
            for j in range(i + 1, len(diseases)):
                disease_a = diseases[i]
                disease_b = diseases[j]

                do_eat_a = set(all_food_advice[disease_a]['宜吃'])
                not_eat_b = set(all_food_advice[disease_b]['忌吃'])

                conflict = do_eat_a & not_eat_b
                if conflict:
                    conflicts.append({
                        '疾病A': disease_a,
                        '疾病B': disease_b,
                        '冲突食物': list(conflict)
                    })

        return {
            '各疾病饮食建议': all_food_advice,
            '饮食冲突': conflicts
        }

    def comprehensive_retrieve(self, disease_name):
        """综合检索"""
        if self._mode == 'neo4j' and self.connected:
            if not self.connected:
                print("Neo4j数据库未连接，无法进行综合检索")
                return None

        print(f"\n正在检索疾病【{disease_name}】的相关知识...")

        try:
            disease_info = self.retrieve_disease_info(disease_name)

            if not disease_info:
                print(f"- 未检索到疾病【{disease_name}】的相关知识")
                print("建议：请确认疾病名称是否正确，或尝试使用疾病的简称")
                return None

            knowledge = {
                '疾病信息': disease_info,
                '症状': self.retrieve_symptoms(disease_name),
                '用药建议': self.retrieve_drugs(disease_name),
                '饮食建议': self.retrieve_food_advice(disease_name),
                '就诊科室': self.retrieve_departments(disease_name),
                '检查项目': self.retrieve_checks(disease_name)
            }

            print("+ 知识检索完成")
            return knowledge

        except Exception as e:
            print(f"- 检索过程中出错: {e}")
            return None

    def get_mode(self):
        """获取当前模式（neo4j 或 json）"""
        return self._mode or 'none'


def main():
    """测试检索功能"""
    print("=" * 50)
    print("医疗知识RAG检索模块 - 测试")
    print("=" * 50)

    retriever = MedicalRAGRetriever()

    print(f"\n当前模式: {retriever.get_mode()}")

    # 测试单疾病检索
    print("\n【测试1】单疾病综合检索")
    knowledge = retriever.comprehensive_retrieve("高血压")

    if knowledge:
        print("\n检索结果：")
        desc = knowledge['疾病信息'].get('desc', '无')
        print(f"  疾病描述: {desc[:100]}...")
        print(f"  症状: {', '.join(knowledge['症状'][:5])}")
        print(f"  推荐药物: {', '.join(knowledge['用药建议']['推荐药物'][:5])}")
        print(f"  常用药物: {', '.join(knowledge['用药建议']['常用药物'][:5])}")
        print(f"  宜吃食物: {', '.join(knowledge['饮食建议']['宜吃'][:5])}")
        print(f"  忌吃食物: {', '.join(knowledge['饮食建议']['忌吃'][:5])}")
        print(f"  就诊科室: {', '.join(knowledge['就诊科室'][:5])}")
        print(f"  检查项目: {', '.join(knowledge['检查项目'][:5])}")

    # 测试多疾病饮食冲突检查
    print("\n\n【测试2】多疾病饮食冲突检查")
    result = retriever.check_food_conflict(["糖尿病", "高血压"])

    if result['饮食冲突']:
        print("  发现饮食冲突：")
        for conflict in result['饮食冲突']:
            print(f"    {conflict['疾病A']} 与 {conflict['疾病B']}")
            print(f"    冲突食物: {', '.join(conflict['冲突食物'])}")
    else:
        print("  未发现明显饮食冲突")


if __name__ == "__main__":
    main()
