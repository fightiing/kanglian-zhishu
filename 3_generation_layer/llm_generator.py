#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大模型集成模块
功能：使用Ollama接入DeepSeek模型，基于RAG检索的知识生成自然语言回答
核心：避免大模型幻觉，仅基于检索到的知识图谱内容生成回答
"""

import requests
import json
import os


class DeepSeekAPILLM:
    """DeepSeek大模型接口（通过官方API，适用于云端部署）"""
    
    def __init__(self, api_key=None, model="deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.connected = bool(self.api_key)
        if self.connected:
            print("OK DeepSeek API 连接成功")
        else:
            print("WARNING DeepSeek API Key 未配置，将使用知识图谱降级回答")
    
    def generate_response(self, prompt, temperature=0.3, max_tokens=1024, knowledge=None):
        if not self.connected:
            return self._build_fallback_response(knowledge)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                return self._build_fallback_response(knowledge)
        except Exception:
            return self._build_fallback_response(knowledge)
    
    def _build_fallback_response(self, knowledge):
        if not knowledge:
            return "抱歉，暂时无法获取详细信息。请稍后重试或咨询医生。"
        
        disease_info = knowledge.get('疾病信息', {})
        drug_info = knowledge.get('用药建议', {})
        food_info = knowledge.get('饮食建议', {})
        symptoms = knowledge.get('症状', [])
        departments = knowledge.get('就诊科室', [])
        
        response_parts = []
        disease_name = disease_info.get('name', '该疾病')
        response_parts.append(f"根据知识图谱查询结果，关于{disease_name}的建议如下：")
        response_parts.append("")
        
        desc = disease_info.get('desc', '')
        if desc and desc != '暂无描述':
            response_parts.append(f"【疾病简介】{desc[:150]}..." if len(desc) > 150 else f"【疾病简介】{desc}")
            response_parts.append("")
        
        if symptoms:
            response_parts.append(f"【常见症状】{', '.join(symptoms[:8])}")
            response_parts.append("")
        
        all_drugs = list(dict.fromkeys(drug_info.get('推荐药物', []) + drug_info.get('常用药物', [])))
        if all_drugs:
            response_parts.append(f"【推荐药物】{', '.join(all_drugs[:8])}")
            response_parts.append("（仅供参考，具体用药请遵医嘱）")
            response_parts.append("")
        
        do_eat = food_info.get('宜吃', [])
        not_eat = food_info.get('忌吃', [])
        if do_eat:
            response_parts.append(f"【宜吃食物】{', '.join(do_eat[:8])}")
        if not_eat:
            response_parts.append(f"【忌吃食物】{', '.join(not_eat[:8])}")
        if do_eat or not_eat:
            response_parts.append("")
        
        if departments:
            response_parts.append(f"【建议就诊科室】{', '.join(departments)}")
            response_parts.append("")
        
        response_parts.append("【重要提醒】以上信息仅供参考，具体诊疗方案请咨询专业医生。")
        return "\n".join(response_parts)


class DeepSeekLLM:
    """DeepSeek大模型接口（通过Ollama）"""
    
    def __init__(self, base_url="http://localhost:11434", model="deepseek-r1:8b"):
        """
        初始化Ollama DeepSeek连接
        Args:
            base_url: Ollama服务地址
            model: 使用的模型名称（默认deepseek-r1:1.5b）
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
        
        # 测试连接
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"OK Ollama服务连接成功")
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if any(model in name for name in model_names):
                    print(f"OK 模型 {model} 已就绪")
                else:
                    print(f"WARNING 警告: 未找到模型 {model}")
                    print(f"  可用模型: {', '.join(model_names)}")
                    print(f"  请运行: ollama pull {model}")
            else:
                print(f"ERROR Ollama服务连接失败")
        except Exception as e:
            print(f"ERROR Ollama服务连接失败: {e}")
            print("请确保Ollama已启动（执行: ollama serve）")
    
    def generate_response(self, prompt, temperature=0.3, max_tokens=1024, knowledge=None):
        """
        生成回答
        Args:
            prompt: 输入提示词
            temperature: 生成温度（0-1，越低越确定性）
            max_tokens: 最大生成长度
            knowledge: 知识图谱检索结果（用于fallback回答）
        Returns:
            生成的文本
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            # 设置60秒超时，给大模型足够的时间来生成回答
            response = requests.post(self.api_url, json=payload, timeout=60)
                    
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                # 模型调用失败时，返回基于知识图谱的fallback回答
                return self._build_fallback_response(knowledge)
                        
        except requests.exceptions.Timeout:
            # 模型调用超时时，返回基于知识图谱的fallback回答
            return self._build_fallback_response(knowledge)
        except Exception as e:
            # 发生异常时，返回基于知识图谱的fallback回答
            return self._build_fallback_response(knowledge)
    
    def _build_fallback_response(self, knowledge):
        """
        基于知识图谱内容构建fallback回答
        Args:
            knowledge: 知识图谱检索结果
        Returns:
            基于实际知识的回答
        """
        if not knowledge:
            return "抱歉，暂时无法获取详细信息。请稍后重试或咨询医生。"
        
        # 提取知识内容
        disease_info = knowledge.get('疾病信息', {})
        drug_info = knowledge.get('用药建议', {})
        food_info = knowledge.get('饮食建议', {})
        symptoms = knowledge.get('症状', [])
        departments = knowledge.get('就诊科室', [])
        
        # 构建基于实际知识的回答
        response_parts = []
        
        # 疾病名称和描述
        disease_name = disease_info.get('name', '该疾病')
        response_parts.append(f"根据知识图谱查询结果，关于{disease_name}的建议如下：")
        response_parts.append("")
        
        # 疾病描述
        desc = disease_info.get('desc', '')
        if desc and desc != '暂无描述':
            response_parts.append(f"【疾病简介】{desc[:150]}..." if len(desc) > 150 else f"【疾病简介】{desc}")
            response_parts.append("")
        
        # 症状
        if symptoms:
            response_parts.append(f"【常见症状】{', '.join(symptoms[:8])}")
            response_parts.append("")
        
        # 推荐药物
        recommend_drugs = drug_info.get('推荐药物', [])
        common_drugs = drug_info.get('常用药物', [])
        all_drugs = list(dict.fromkeys(recommend_drugs + common_drugs))  # 去重
        if all_drugs:
            response_parts.append(f"【推荐药物】{', '.join(all_drugs[:8])}")
            response_parts.append("（仅供参考，具体用药请遵医嘱）")
            response_parts.append("")
        
        # 饮食建议
        do_eat = food_info.get('宜吃', [])
        not_eat = food_info.get('忌吃', [])
        if do_eat:
            response_parts.append(f"【宜吃食物】{', '.join(do_eat[:8])}")
        if not_eat:
            response_parts.append(f"【忌吃食物】{', '.join(not_eat[:8])}")
        if do_eat or not_eat:
            response_parts.append("")
        
        # 就诊科室
        if departments:
            response_parts.append(f"【建议就诊科室】{', '.join(departments)}")
            response_parts.append("")
        
        # 通用提醒
        response_parts.append("【重要提醒】以上信息仅供参考，具体诊疗方案请咨询专业医生。")
        
        return "\n".join(response_parts)

class MedicalAssistant:
    """医疗助手（RAG + LLM）"""
    
    def __init__(self, retriever, llm):
        """
        初始化医疗助手
        Args:
            retriever: RAG检索器
            llm: 大模型
        """
        self.retriever = retriever
        self.llm = llm
    
    def build_prompt(self, query, knowledge):
        """
        构建Prompt（核心：限制大模型只使用检索到的知识）
        Args:
            query: 用户问题
            knowledge: RAG检索到的知识
        Returns:
            完整的Prompt
        """
        # 严格的Prompt模板：禁止大模型使用外部知识
        prompt_template = """你是一个专业的医疗咨询助手。请**严格基于以下提供的知识图谱内容**回答用户问题，不要添加任何知识图谱中没有的信息。

【知识图谱检索结果】
疾病名称：{disease_name}
疾病描述：{description}

症状表现：{symptoms}

推荐药物：{recommend_drugs}
常用药物：{common_drugs}

饮食建议：
- 宜吃：{do_eat}
- 忌吃：{not_eat}

就诊科室：{departments}

治疗周期：{cure_time}
治愈率：{cure_rate}

【用户问题】
{query}

【回答要求】
1. 只使用上述知识图谱中的信息，不要编造或推测
2. 如果知识图谱中没有相关信息，明确说明"知识图谱中暂无该信息"
3. 用通俗易懂的语言解释，适合普通患者理解
4. 涉及用药时，提醒"仅供参考，具体用药请遵医嘱"

请回答："""
        
        # 提取知识内容
        disease_info = knowledge.get('疾病信息', {})
        drug_info = knowledge.get('用药建议', {})
        food_info = knowledge.get('饮食建议', {})
        
        # 填充模板
        prompt = prompt_template.format(
            disease_name=disease_info.get('name', '未知'),
            description=disease_info.get('desc', '暂无描述')[:500],  # 限制长度
            symptoms='、'.join(knowledge.get('症状', [])[:10]) or '暂无',
            recommend_drugs='、'.join(drug_info.get('推荐药物', [])[:8]) or '暂无',
            common_drugs='、'.join(drug_info.get('常用药物', [])[:8]) or '暂无',
            do_eat='、'.join(food_info.get('宜吃', [])[:10]) or '暂无',
            not_eat='、'.join(food_info.get('忌吃', [])[:10]) or '暂无',
            departments='、'.join(knowledge.get('就诊科室', [])) or '暂无',
            cure_time=disease_info.get('cure_lasttime', '暂无'),
            cure_rate=disease_info.get('cured_prob', '暂无'),
            query=query
        )
        
        return prompt
    
    def answer_question(self, disease_name, user_query):
        """
        回答用户问题（完整流程：检索->生成）
        Args:
            disease_name: 疾病名称
            user_query: 用户问题
        Returns:
            大模型生成的回答
        """
        print(f"\n{'='*60}")
        print(f"用户问题：{user_query}")
        print(f"{'='*60}")
        
        # 步骤1：RAG检索知识
        print("\n[步骤1] RAG检索知识图谱...")
        knowledge = self.retriever.comprehensive_retrieve(disease_name)
        
        if not knowledge:
            return "抱歉，未检索到相关医疗知识，请确认疾病名称是否正确。"
        
        # 步骤2：构建Prompt
        print("[步骤2] 构建知识上下文Prompt...")
        prompt = self.build_prompt(user_query, knowledge)
        
        # 步骤3：大模型生成回答（可能需要等待较长时间，请耐心）
        print("[步骤3] DeepSeek模型生成回答（最长等待60秒）...")
        response = self.llm.generate_response(prompt, temperature=0.3, knowledge=knowledge)
        
        print(f"\n{'='*60}")
        print("系统回答：")
        print(f"{'='*60}")
        print(response)
        print(f"{'='*60}\n")
        
        return response
    
    def multi_disease_consultation(self, disease_list, user_query):
        """
        多疾病联合咨询（核心场景：慢病患者多疾病用药安全）
        Args:
            disease_list: 疾病列表
            user_query: 用户问题
        Returns:
            综合回答
        """
        print(f"\n{'='*60}")
        print(f"多疾病咨询：{', '.join(disease_list)}")
        print(f"用户问题：{user_query}")
        print(f"{'='*60}")
        
        # 检索多疾病的用药和饮食信息
        print("\n[步骤1] 检索多疾病用药和饮食信息...")
        
        all_knowledge = {}
        for disease in disease_list:
            knowledge = self.retriever.comprehensive_retrieve(disease)
            if knowledge:
                all_knowledge[disease] = knowledge
        
        if not all_knowledge:
            return "抱歉，未检索到相关疾病信息。"
        
        # 检查饮食冲突
        print("[步骤2] 分析多疾病饮食冲突...")
        food_conflict = self.retriever.check_food_conflict(disease_list)
        
        # 构建多疾病Prompt
        print("[步骤3] 构建多疾病知识上下文...")
        
        knowledge_summary = "【多疾病知识图谱检索结果】\n\n"
        
        for disease, knowledge in all_knowledge.items():
            disease_info = knowledge.get('疾病信息', {})
            drug_info = knowledge.get('用药建议', {})
            food_info = knowledge.get('饮食建议', {})
            
            knowledge_summary += f"## {disease}\n"
            knowledge_summary += f"推荐药物：{'、'.join(drug_info.get('推荐药物', [])[:5]) or '暂无'}\n"
            knowledge_summary += f"宜吃：{'、'.join(food_info.get('宜吃', [])[:5]) or '暂无'}\n"
            knowledge_summary += f"忌吃：{'、'.join(food_info.get('忌吃', [])[:5]) or '暂无'}\n\n"
        
        # 添加冲突信息
        if food_conflict['饮食冲突']:
            knowledge_summary += "【警告】发现饮食冲突：\n"
            for conflict in food_conflict['饮食冲突']:
                knowledge_summary += f"- {conflict['疾病A']} 与 {conflict['疾病B']} 存在冲突食物：{'、'.join(conflict['冲突食物'])}\n"
        
        prompt = f"""{knowledge_summary}

【用户问题】
{user_query}

【回答要求】
1. 针对多疾病患者，综合考虑各疾病的用药和饮食建议
2. 重点提示可能的用药冲突和饮食冲突
3. 只使用知识图谱中的信息，不编造内容
4. 提醒"具体用药请咨询医生"

请回答："""
        
        # 大模型生成回答（可能需要较长时间，请耐心等待）
        print("[步骤4] DeepSeek模型生成综合回答（最长等待60秒）...")
        # 对于多疾病咨询，使用第一个疾病的知识作为fallback
        first_knowledge = list(all_knowledge.values())[0] if all_knowledge else None
        response = self.llm.generate_response(prompt, temperature=0.3, knowledge=first_knowledge)
        
        print(f"\n{'='*60}")
        print("系统回答：")
        print(f"{'='*60}")
        print(response)
        print(f"{'='*60}\n")
        
        return response


def main():
    """测试大模型集成"""
    print("="*60)
    print("大模型集成模块 - 测试")
    print("="*60)
    
    from medical_rag_retriever import MedicalRAGRetriever
    
    # 初始化组件
    print("\n初始化系统组件...")
    retriever = MedicalRAGRetriever()
    llm = DeepSeekLLM(model="deepseek-r1:7b")
    assistant = MedicalAssistant(retriever, llm)
    
    # 测试单疾病咨询
    print("\n\n【测试1】单疾病咨询")
    assistant.answer_question(
        disease_name="高血压",
        user_query="高血压患者在饮食上应该注意什么？"
    )
    
    # 测试多疾病咨询
    print("\n\n【测试2】多疾病咨询（慢病患者典型场景）")
    assistant.multi_disease_consultation(
        disease_list=["糖尿病", "高血压"],
        user_query="我同时患有糖尿病和高血压，在饮食和用药上有什么需要特别注意的吗？"
    )


if __name__ == "__main__":
    main()
