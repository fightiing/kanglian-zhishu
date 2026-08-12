#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
数据层 (Data Layer)
================================================================================
职责：知识图谱数据存储与管理
功能：
  - kg_builder: 构建Neo4j知识图谱（从medical.json导入）
  - neo4j_connector: Neo4j数据库连接管理

使用示例：
    from data_layer.kg_builder import MedicalKGBuilder
    
    builder = MedicalKGBuilder()
    builder.load_medical_data("medical.json")
    builder.build_knowledge_graph(data)
================================================================================
"""

from .kg_builder import MedicalKGBuilder

__all__ = ['MedicalKGBuilder']
