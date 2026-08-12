#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepSeek RAG服务 - 使用官方API
"""

import requests
import json
import time
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DeepSeekRAGService:
    """DeepSeek RAG服务 - 使用官方API"""

    def __init__(self, api_key: str = "sk-f2fbccb9fd5b45eb82143e99d4c2f1da"):
        # API密钥和端点配置
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"

        # 超时设置
        self.timeout = 30
        self.connect_timeout = 10
        self.max_retries = 3

        # 请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 医疗知识库初始化
        self.medical_knowledge_base = self._load_medical_knowledge()

        logger.info("✓ DeepSeek RAG服务初始化完成")

    def _load_medical_knowledge(self) -> List[Dict]:
        """加载医疗知识库"""
        return [
            {
                "id": "MED001",
                "category": "头晕/眩晕",
                "content": "头晕可能原因：1.耳石症（体位性眩晕）；2.颈椎病；3.贫血；4.低血压。建议：测量血压，如持续头晕建议就医神经内科。",
                "keywords": ["头晕", "眩晕", "头昏", "站立不稳"],
                "severity": "需评估"
            },
            {
                "id": "MED002",
                "category": "感冒",
                "content": "感冒症状：流鼻涕、打喷嚏、喉咙痛、咳嗽、轻微发热。建议：多休息、多喝水，可服用感冒药缓解症状，如发热超过38.5℃建议就医。",
                "keywords": ["感冒", "流鼻涕", "打喷嚏", "咳嗽", "发热"],
                "severity": "轻度"
            },
            {
                "id": "MED003",
                "category": "高血压",
                "content": "高血压症状：头晕、头痛、心悸、视力模糊。建议：定期监测血压，低盐饮食，按时服药，建议就诊心内科。",
                "keywords": ["高血压", "头晕", "心悸", "头痛", "视力模糊"],
                "severity": "需就医"
            },
            {
                "id": "MED004",
                "category": "糖尿病",
                "content": "糖尿病症状：多饮、多食、多尿、体重下降。建议：监测血糖，控制饮食，适当运动，建议就诊内分泌科。",
                "keywords": ["糖尿病", "多饮", "多食", "多尿", "体重下降"],
                "severity": "需就医"
            },
            {
                "id": "MED005",
                "category": "冠心病",
                "content": "冠心病症状：胸痛、胸闷、心悸、呼吸困难。紧急提示：如出现剧烈胸痛请立即就医！建议就诊心内科。",
                "keywords": ["冠心病", "胸痛", "胸闷", "心悸", "呼吸困难"],
                "severity": "紧急"
            }
        ]

    def search_medical_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索医疗知识库"""
        try:
            query_lower = query.lower()
            results = []

            for doc in self.medical_knowledge_base:
                score = 0
                keywords_matched = []

                for keyword in doc["keywords"]:
                    if keyword in query_lower:
                        score += 2
                        keywords_matched.append(keyword)

                # 检查疾病类别匹配
                category = doc["category"].lower()
                if category in query_lower:
                    score += 3

                if score > 0:
                    results.append({
                        "content": doc["content"],
                        "category": doc["category"],
                        "score": score,
                        "keywords_matched": keywords_matched[:3],
                        "severity": doc.get("severity", "需评估")
                    })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"搜索医疗知识失败: {e}")
            return []

    def ask_question(self, question: str) -> str:
        """
        向DeepSeek API提问

        Args:
            question: 用户问题

        Returns:
            AI回答
        """
        # 搜索相关医疗知识
        relevant_docs = self.search_medical_knowledge(question, top_k=2)

        # 构建增强提示
        system_prompt = "你是一个专业的医疗AI助手，请基于提供的医疗知识进行回答。"
        context_parts = ["📚 相关医疗知识："]

        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"\n{i}. 【{doc['category']} - 严重程度: {doc['severity']}】")
            context_parts.append(f"   {doc['content']}")

        context_text = "\n".join(context_parts) if len(context_parts) > 1 else "暂无相关医疗知识"

        full_question = f"""{context_text}

用户问：{question}

请基于以上信息，用中文专业、准确、易懂地回答用户的医疗咨询问题。"""

        # 请求数据
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_question}
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
            "stream": False
        }

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=(self.connect_timeout, self.timeout)
                )

                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()

                elif response.status_code == 429:
                    # 频率限制，等待后重试
                    wait_time = 2 ** attempt
                    logger.info(f"频率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.error(f"API错误: {response.status_code} - {response.text}")
                    return f"AI服务暂时不可用，请稍后重试"

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.info(f"请求超时，第 {attempt + 1} 次重试...")
                    continue
                return "请求超时，请稍后重试"

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.info(f"网络错误: {e}，第 {attempt + 1} 次重试...")
                    continue
                return f"网络错误: {str(e)}"

        return "服务暂时不可用，请稍后重试"


# 创建全局实例
deepseek_rag_service = DeepSeekRAGService()