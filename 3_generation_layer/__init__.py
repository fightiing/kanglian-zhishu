#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
生成层 (Generation Layer - LLM)
================================================================================
职责：基于检索到的知识，使用大模型生成自然语言答复
功能：
  - llm_generator: DeepSeek模型集成，生成医疗咨询答复

使用示例：
    from generation_layer.llm_generator import DeepSeekLLM, MedicalAssistant
    
    llm = DeepSeekLLM()
    assistant = MedicalAssistant(retriever, llm)
    
    # 单疾病咨询
    answer = assistant.answer_question(
        disease_name="高血压",
        user_query="需要注意什么？"
    )
    
    # 多疾病咨询
    answer = assistant.multi_disease_consultation(
        disease_list=["糖尿病", "高血压"],
        user_query="用药和饮食需要注意什么？"
    )
================================================================================
"""

from .llm_generator import DeepSeekLLM, MedicalAssistant

__all__ = ['DeepSeekLLM', 'MedicalAssistant']
