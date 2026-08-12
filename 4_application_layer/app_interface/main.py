#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
康联智枢——面向主动健康的知识驱动医疗智能协同网络 - 主程序
应用场景：社区医生日均接诊30+慢病患者，需快速匹配多疾病合并用药的禁忌关系
系统架构：知识图谱（Neo4j）+ RAG检索 + 大模型生成（Ollama DeepSeek）
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rag_module.medical_rag_retriever import MedicalRAGRetriever
from llm_module.deepseek_llm import DeepSeekLLM, MedicalAssistant


def print_welcome():
    """显示欢迎界面"""
    print("\n" + "="*70)
    print(" "*15 + "康联智枢——面向主动健康的知识驱动医疗智能协同网络")
    print("="*70)
    print("\n【应用场景】")
    print("  目标用户：社区医生、基层医疗工作者")
    print("  核心痛点：日均接诊30+慢病患者，难快速匹配'多疾病合并用药'的")
    print("            禁忌关系，存在用药风险和饮食冲突")
    print("\n【功能目标】")
    print("  1. 快速检索疾病的用药建议和饮食禁忌")
    print("  2. 智能分析多疾病患者的用药冲突和饮食冲突")
    print("  3. 基于知识图谱生成专业的医疗咨询建议")
    print("\n【技术架构】")
    print("  数据层：Neo4j知识图谱（500+疾病，10000+关系）")
    print("  检索层：RAG关键词+图关系检索")
    print("  生成层：DeepSeek模型（通过Ollama本地部署）")
    print("  应用层：命令行交互界面")
    print("="*70 + "\n")


def print_menu():
    """显示功能菜单"""
    print("\n【功能菜单】")
    print("  1. 单疾病咨询（查询疾病的症状、用药、饮食建议）")
    print("  2. 多疾病联合咨询（分析多疾病用药冲突和饮食冲突）")
    print("  3. 快速用药查询（仅显示推荐药物和常用药物）")
    print("  4. 饮食禁忌查询（仅显示宜吃和忌吃食物）")
    print("  5. 退出系统")
    print("-"*70)


def single_disease_consultation(assistant):
    """单疾病咨询"""
    print("\n" + "="*70)
    print("【单疾病咨询】")
    print("="*70)
    
    disease_name = input("\n请输入疾病名称（如：高血压、糖尿病）：").strip()
    
    if not disease_name:
        print("✗ 疾病名称不能为空")
        return
    
    user_query = input("请输入您的问题（如：需要注意什么？）：").strip()
    
    if not user_query:
        user_query = f"{disease_name}患者需要注意什么？"
    
    assistant.answer_question(disease_name, user_query)


def multi_disease_consultation(assistant):
    """多疾病联合咨询"""
    print("\n" + "="*70)
    print("【多疾病联合咨询】")
    print("="*70)
    
    diseases_input = input("\n请输入多个疾病名称（用逗号分隔，如：糖尿病,高血压）：").strip()
    
    if not diseases_input:
        print("✗ 疾病名称不能为空")
        return
    
    disease_list = [d.strip() for d in diseases_input.split(',')]
    
    print(f"\n分析疾病：{', '.join(disease_list)}")
    
    user_query = input("请输入您的问题（如：用药和饮食需要注意什么？）：").strip()
    
    if not user_query:
        user_query = f"患有{', '.join(disease_list)}，在用药和饮食上需要注意什么？"
    
    assistant.multi_disease_consultation(disease_list, user_query)


def quick_drug_query(retriever):
    """快速用药查询"""
    print("\n" + "="*70)
    print("【快速用药查询】")
    print("="*70)
    
    disease_name = input("\n请输入疾病名称：").strip()
    
    if not disease_name:
        print("✗ 疾病名称不能为空")
        return
    
    print(f"\n正在查询【{disease_name}】的用药信息...")
    
    drugs = retriever.retrieve_drugs(disease_name)
    
    print(f"\n{'='*70}")
    print(f"【{disease_name}】用药信息")
    print(f"{'='*70}")
    
    if drugs['推荐药物']:
        print("\n推荐药物：")
        for i, drug in enumerate(drugs['推荐药物'][:10], 1):
            print(f"  {i}. {drug}")
    else:
        print("\n推荐药物：暂无")
    
    if drugs['常用药物']:
        print("\n常用药物：")
        for i, drug in enumerate(drugs['常用药物'][:10], 1):
            print(f"  {i}. {drug}")
    else:
        print("\n常用药物：暂无")
    
    print(f"\n{'='*70}")
    print("⚠ 提示：以上信息仅供参考，具体用药请遵医嘱")
    print(f"{'='*70}\n")


def food_advice_query(retriever):
    """饮食禁忌查询"""
    print("\n" + "="*70)
    print("【饮食禁忌查询】")
    print("="*70)
    
    disease_name = input("\n请输入疾病名称：").strip()
    
    if not disease_name:
        print("✗ 疾病名称不能为空")
        return
    
    print(f"\n正在查询【{disease_name}】的饮食建议...")
    
    food_advice = retriever.retrieve_food_advice(disease_name)
    
    print(f"\n{'='*70}")
    print(f"【{disease_name}】饮食建议")
    print(f"{'='*70}")
    
    if food_advice['宜吃']:
        print("\n✓ 宜吃食物：")
        for i, food in enumerate(food_advice['宜吃'][:15], 1):
            print(f"  {i}. {food}", end="  ")
            if i % 5 == 0:
                print()
        print()
    else:
        print("\n✓ 宜吃食物：暂无")
    
    if food_advice['忌吃']:
        print("\n✗ 忌吃食物：")
        for i, food in enumerate(food_advice['忌吃'][:15], 1):
            print(f"  {i}. {food}", end="  ")
            if i % 5 == 0:
                print()
        print()
    else:
        print("\n✗ 忌吃食物：暂无")
    
    print(f"\n{'='*70}\n")


def main():
    """主函数"""
    # 显示欢迎信息
    print_welcome()
    
    # 初始化系统组件
    print("正在初始化系统组件...\n")
    
    try:
        print("[1/3] 连接Neo4j知识图谱...")
        retriever = MedicalRAGRetriever()
        
        print("\n[2/3] 连接Ollama DeepSeek模型...")
        llm = DeepSeekLLM(model="deepseek-r1:8b")
        
        print("\n[3/3] 初始化医疗助手...")
        assistant = MedicalAssistant(retriever, llm)
        
        print("\n✓ 系统初始化完成！\n")
        
    except Exception as e:
        print(f"\n✗ 系统初始化失败: {e}")
        print("\n请检查：")
        print("  1. Neo4j服务是否已启动（执行：neo4j.bat console）")
        print("  2. 知识图谱是否已构建（执行：kg_construction/build_medical_kg.py）")
        print("  3. Ollama服务是否已启动（执行：ollama serve）")
        print("  4. DeepSeek模型是否已下载（执行：ollama pull deepseek-r1:1.5b）")
        return
    
    # 主循环
    while True:
        print_menu()
        
        choice = input("请选择功能（输入数字1-5）：").strip()
        
        if choice == '1':
            single_disease_consultation(assistant)
        elif choice == '2':
            multi_disease_consultation(assistant)
        elif choice == '3':
            quick_drug_query(retriever)
        elif choice == '4':
            food_advice_query(retriever)
        elif choice == '5':
            print("\n感谢使用康联智枢——面向主动健康的知识驱动医疗智能协同网络！")
            print("祝您工作顺利！\n")
            break
        else:
            print("\n✗ 无效选择，请输入1-5之间的数字\n")


if __name__ == "__main__":
    main()
