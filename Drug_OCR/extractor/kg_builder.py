"""药品说明书知识图谱构建工具

@author: wsy
@date: 2026.01.07
@desc: 将NER识别结果转换为知识图谱三元组
"""

from typing import Dict, List


def build_kg_triples(ner_result: Dict) -> List[Dict]:
    """构建药品知识图谱三元组
    
    Args:
        ner_result: NER识别结果字典，包含:
            - drug: 药品名称列表
            - indication: 适应症列表
            - risk_disease: 风险疾病列表  
            - population: 适用人群列表
            - adverse_reaction: 不良反应列表
            - interaction: 相互作用列表
            
    Returns:
        List[Dict]: 知识图谱三元组列表，每个元素包含:
            - 头实体: 药品名称
            - 关系: 关系类型
            - 尾实体: 关联实体
            - 类型: 关系分类
    """
    triples = []  # 存储生成的三元组

    drugs = ner_result.get("drug", [])

    for drug in drugs:
        for ind in ner_result.get("indication", []):
            triples.append({
                "头实体": drug,
                "关系": "功能主治",
                "尾实体": ind,
                "类型": "治疗"
            })

        for risk in ner_result.get("risk_disease", []):
            triples.append({
                "头实体": drug,
                "关系": "慎用人群/疾病",
                "尾实体": risk,
                "类型": "风险"
            })

        for pop in ner_result.get("population", []):
            triples.append({
                "头实体": drug,
                "关系": "适用/慎用人群",
                "尾实体": pop,
                "类型": "人群"
            })

        for adv in ner_result.get("adverse_reaction", []):
            triples.append({
                "头实体": drug,
                "关系": "不良反应",
                "尾实体": adv,
                "类型": "安全性"
            })

        for it in ner_result.get("interaction", []):
            triples.append({
                "头实体": drug,
                "关系": "相互作用",
                "尾实体": it,
                "类型": "用药冲突"
            })

    return triples
