#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
检索层 (Retrieval Layer - RAG)
================================================================================
职责：从知识图谱检索相关医疗知识
功能：
  - rag_retriever: RAG检索器，支持单疾病/多疾病检索

使用示例：
    from retrieval_layer.rag_retriever import MedicalRAGRetriever
    
    retriever = MedicalRAGRetriever()
    
    # 单疾病检索
    knowledge = retriever.comprehensive_retrieve("高血压")
    
    # 多疾病冲突检查
    conflicts = retriever.check_food_conflict(["糖尿病", "高血压"])
================================================================================
"""

from .rag_retriever import MedicalRAGRetriever

__all__ = ['MedicalRAGRetriever']
