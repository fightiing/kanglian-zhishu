#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医生推荐系统 - 优化增强版
支持知识图谱匹配 + AI分析 + 向量化快速匹配
"""

import logging
import time
import re
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba  # 中文分词

logger = logging.getLogger(__name__)


class OptimizedDoctorRecommendationSystem:
    """优化版医生推荐系统 - 支持向量化快速匹配"""

    def __init__(self, retriever, deepseek_rag=None):
        """
        初始化优化版医生推荐系统

        Args:
            retriever: 医学知识图谱检索器
            deepseek_rag: DeepSeek RAG服务（可选）
        """
        self.retriever = retriever
        self.deepseek_rag = deepseek_rag

        # 初始化优化组件
        self.vectorizer = None
        self.doctor_vectors = None
        self.symptom_index = {}

        # 模拟医生数据库
        self.doctors = self._init_enhanced_doctor_database()

        # 症状关键词到科室的映射（扩展版）
        self.symptom_to_department = self._init_symptom_mapping()

        # 初始化优化组件
        self._initialize_optimization_components()

        logger.info("✓ 优化版医生推荐系统初始化完成")

    def _init_enhanced_doctor_database(self) -> List[Dict]:
        """初始化增强版医生数据库"""
        doctors = [
            {
                'id': 1, 'name': '王明德', 'title': '主任医师', 'specialty': '心内科',
                'hospital': '北京协和医院', 'experience': 20, 'rating': 4.8,
                'distance': 1.2, 'schedule': '周一至周五 上午8:00-12:00',
                'expertise': ['冠心病', '高血压', '心力衰竭', '心律失常'],
                'keywords': '心内科 冠心病 高血压 心力衰竭 心律失常 心血管',
                'available': True, 'patient_volume': 1500
            },
            {
                'id': 2, 'name': '李华', 'title': '副主任医师', 'specialty': '心血管内科',
                'hospital': '北京大学人民医院', 'experience': 15, 'rating': 4.7,
                'distance': 2.5, 'schedule': '周二至周六 下午14:00-17:00',
                'expertise': ['心律失常', '心肌病', '心脏康复', '冠心病'],
                'keywords': '心血管内科 心律失常 心肌病 心脏康复 冠心病',
                'available': True, 'patient_volume': 1200
            },
            {
                'id': 3, 'name': '张伟', 'title': '主治医师', 'specialty': '全科',
                'hospital': '朝阳社区卫生服务中心', 'experience': 8, 'rating': 4.5,
                'distance': 0.8, 'schedule': '周一至周日 全天',
                'expertise': ['常见病', '慢病管理', '健康咨询', '高血压', '糖尿病'],
                'keywords': '全科 常见病 慢病管理 健康咨询 高血压 糖尿病',
                'available': True, 'patient_volume': 800
            },
            {
                'id': 4, 'name': '陈静', 'title': '主任医师', 'specialty': '神经内科',
                'hospital': '北京天坛医院', 'experience': 18, 'rating': 4.9,
                'distance': 3.2, 'schedule': '周一、周三、周五 上午',
                'expertise': ['中风', '帕金森', '头痛', '头晕', '失眠'],
                'keywords': '神经内科 中风 帕金森 头痛 头晕 失眠 神经系统',
                'available': True, 'patient_volume': 1800
            },
            {
                'id': 5, 'name': '刘强', 'title': '副主任医师', 'specialty': '呼吸内科',
                'hospital': '北京中日友好医院', 'experience': 12, 'rating': 4.6,
                'distance': 1.8, 'schedule': '周二、周四、周六 全天',
                'expertise': ['肺炎', '哮喘', '慢阻肺', '咳嗽', '呼吸困难'],
                'keywords': '呼吸内科 肺炎 哮喘 慢阻肺 咳嗽 呼吸困难 呼吸道',
                'available': True, 'patient_volume': 1100
            },
            {
                'id': 6, 'name': '赵敏', 'title': '主任医师', 'specialty': '内分泌科',
                'hospital': '北京医院', 'experience': 22, 'rating': 4.8,
                'distance': 2.1, 'schedule': '周一至周四 全天',
                'expertise': ['糖尿病', '甲状腺疾病', '骨质疏松', '肥胖症'],
                'keywords': '内分泌科 糖尿病 甲状腺疾病 骨质疏松 肥胖症 代谢',
                'available': True, 'patient_volume': 1600
            },
            {
                'id': 7, 'name': '孙建国', 'title': '副主任医师', 'specialty': '消化内科',
                'hospital': '北京友谊医院', 'experience': 16, 'rating': 4.7,
                'distance': 1.5, 'schedule': '周一至周五 下午',
                'expertise': ['胃炎', '溃疡', '肝病', '胃痛', '腹痛'],
                'keywords': '消化内科 胃炎 溃疡 肝病 胃痛 腹痛 消化系统',
                'available': True, 'patient_volume': 1300
            },
            {
                'id': 8, 'name': '周小红', 'title': '主治医师', 'specialty': '中医科',
                'hospital': '东直门社区卫生服务中心', 'experience': 10, 'rating': 4.4,
                'distance': 0.5, 'schedule': '周一至周六 上午',
                'expertise': ['中医调理', '针灸', '推拿', '失眠', '乏力'],
                'keywords': '中医科 中医调理 针灸 推拿 失眠 乏力 中医',
                'available': True, 'patient_volume': 900
            },
            {
                'id': 9, 'name': '杨帆', 'title': '副主任医师', 'specialty': '骨科',
                'hospital': '积水潭医院', 'experience': 14, 'rating': 4.6,
                'distance': 2.8, 'schedule': '周一、三、五全天',
                'expertise': ['关节炎', '骨折', '腰痛', '关节痛', '骨质疏松'],
                'keywords': '骨科 关节炎 骨折 腰痛 关节痛 骨质疏松 骨骼',
                'available': True, 'patient_volume': 1000
            },
            {
                'id': 10, 'name': '吴婷', 'title': '主任医师', 'specialty': '皮肤科',
                'hospital': '北京协和医院', 'experience': 19, 'rating': 4.7,
                'distance': 1.2, 'schedule': '周二、四、六上午',
                'expertise': ['湿疹', '皮炎', '痤疮', '过敏', '皮疹'],
                'keywords': '皮肤科 湿疹 皮炎 痤疮 过敏 皮疹 皮肤病',
                'available': True, 'patient_volume': 1400
            }
        ]
        return doctors

    def _init_symptom_mapping(self) -> Dict[str, List[str]]:
        """初始化症状-科室映射表"""
        return {
            '心血管': ['心内科', '心血管内科'],
            '心脏': ['心内科', '心血管内科'],
            '胸痛': ['心内科', '胸外科', '急诊科'],
            '胸闷': ['心内科', '呼吸内科'],
            '心悸': ['心内科', '神经内科'],
            '头晕': ['神经内科', '耳鼻喉科', '心内科'],
            '头痛': ['神经内科', '神经外科', '全科'],
            '发热': ['呼吸内科', '感染科', '全科'],
            '咳嗽': ['呼吸内科', '胸外科'],
            '胃痛': ['消化内科', '胃肠外科'],
            '腹痛': ['消化内科', '普外科', '妇科'],
            '高血压': ['心内科', '高血压科'],
            '糖尿病': ['内分泌科', '糖尿病科'],
            '关节痛': ['骨科', '风湿免疫科'],
            '腰痛': ['骨科', '康复科', '中医科'],
            '失眠': ['神经内科', '精神心理科', '中医科'],
            '抑郁': ['精神科', '心理科', '神经内科'],
            '过敏': ['皮肤科', '变态反应科', '耳鼻喉科'],
            '皮疹': ['皮肤科', '皮肤性病科'],
            '呼吸困难': ['呼吸内科', '急诊科', '心内科'],
            '乏力': ['全科', '神经内科', '内分泌科'],
            '中风': ['神经内科', '急诊科'],
            '帕金森': ['神经内科'],
            '肺炎': ['呼吸内科'],
            '哮喘': ['呼吸内科', '变态反应科'],
            '胃炎': ['消化内科'],
            '溃疡': ['消化内科'],
            '肝病': ['消化内科', '肝病科'],
            '关节炎': ['骨科', '风湿免疫科'],
            '骨折': ['骨科', '急诊科'],
            '湿疹': ['皮肤科'],
            '皮炎': ['皮肤科']
        }

    def _initialize_optimization_components(self):
        """初始化优化组件"""
        try:
            # 初始化TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(
                analyzer='char',
                ngram_range=(1, 3),
                min_df=1,
                max_features=1000
            )

            # 预计算医生特征向量
            doctor_texts = []
            for doctor in self.doctors:
                # 合并医生特征文本
                text_parts = [
                    doctor['specialty'],
                    ' '.join(doctor['expertise']),
                    doctor.get('keywords', '')
                ]
                doctor_text = ' '.join(text_parts)
                doctor_texts.append(doctor_text)

            self.doctor_vectors = self.vectorizer.fit_transform(doctor_texts)

            # 构建症状索引
            self._build_symptom_index()

            logger.info("✓ 向量化组件初始化完成")

        except Exception as e:
            logger.error(f"优化组件初始化失败: {e}")
            # 降级处理
            self.vectorizer = None
            self.doctor_vectors = None

    def _build_symptom_index(self):
        """构建症状索引"""
        try:
            # 从知识图谱获取症状-疾病-科室关系
            query = """
            MATCH (s:症状)-[:症状表现]->(d:疾病)-[:就诊科室]->(dept:科室)
            RETURN s.name as symptom, d.name as disease, dept.name as department
            LIMIT 100
            """
            result = self.retriever.graph.run(query).data()

            for record in result:
                symptom = record['symptom'].lower()
                department = record['department']

                if symptom not in self.symptom_index:
                    self.symptom_index[symptom] = set()
                self.symptom_index[symptom].add(department)

        except Exception as e:
            logger.warning(f"构建症状索引失败: {e}")

    def fast_symptom_match(self, symptom: str, top_k: int = 10) -> List[tuple]:
        """
        快速症状匹配（向量化版本）

        Args:
            symptom: 症状描述
            top_k: 返回前k个最匹配的医生

        Returns:
            [(医生索引, 相似度分数), ...]
        """
        if self.vectorizer is None or self.doctor_vectors is None:
            return self._fallback_symptom_match(symptom, top_k)

        try:
            # 向量化症状描述
            symptom_vector = self.vectorizer.transform([symptom])

            # 计算余弦相似度
            similarities = cosine_similarity(symptom_vector, self.doctor_vectors).flatten()

            # 获取相似度最高的前k个医生
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            return [(idx, float(similarities[idx])) for idx in top_indices]

        except Exception as e:
            logger.error(f"向量匹配失败: {e}")
            return self._fallback_symptom_match(symptom, top_k)

    def _fallback_symptom_match(self, symptom: str, top_k: int) -> List[tuple]:
        """降级匹配算法"""
        symptom_lower = symptom.lower()
        matches = []

        for i, doctor in enumerate(self.doctors):
            score = 0

            # 关键词匹配
            doctor_text = f"{doctor['specialty']} {' '.join(doctor['expertise'])}".lower()

            for keyword in self.symptom_to_department:
                if keyword in symptom_lower and keyword in doctor_text:
                    score += 1

            if score > 0:
                matches.append((i, score))

        # 按分数排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def recommend_doctors_optimized(self, symptom: str, use_ai: bool = True, max_results: int = 5) -> Dict:
        """
        优化版医生推荐（分层过滤 + 向量匹配）

        Args:
            symptom: 症状描述
            use_ai: 是否使用AI增强分析
            max_results: 最大返回结果数

        Returns:
            推荐结果
        """
        start_time = time.time()

        try:
            # 1. 快速科室匹配
            recommended_departments = self._fast_department_match(symptom)

            # 2. 向量化快速匹配
            vector_matches = self.fast_symptom_match(symptom, top_k=20)

            # 3. 分层过滤
            filtered_doctors = self._hierarchical_filter(vector_matches, recommended_departments, symptom)

            # 4. 精细排序
            ranked_doctors = self._optimized_ranking(filtered_doctors, symptom)

            # 5. AI增强分析（可选）
            ai_enhancement = None
            if use_ai and self.deepseek_rag:
                ai_enhancement = self._get_ai_enhancement(symptom, ranked_doctors[:3])

            processing_time = time.time() - start_time

            logger.info(f"推荐完成 - 症状: {symptom}, 耗时: {processing_time:.3f}秒")

            return {
                'success': True,
                'data': {
                    'symptom': symptom,
                    'matched_departments': recommended_departments,
                    'doctors': ranked_doctors[:max_results],
                    'processing_time': processing_time,
                    'ai_enhancement': ai_enhancement,
                    'total_candidates': len(ranked_doctors)
                }
            }

        except Exception as e:
            logger.error(f"推荐失败: {e}")
            return {
                'success': False,
                'message': f'推荐失败: {str(e)}',
                'data': {
                    'symptom': symptom,
                    'doctors': [],
                    'processing_time': time.time() - start_time
                }
            }

    def _fast_department_match(self, symptom: str) -> List[str]:
        """快速科室匹配"""
        departments = set()

        # 1. 使用预建的症状索引
        symptom_lower = symptom.lower()
        for known_symptom, dept_set in self.symptom_index.items():
            if known_symptom in symptom_lower:
                departments.update(dept_set)

        # 2. 关键词匹配
        for keyword, dept_list in self.symptom_to_department.items():
            if keyword in symptom_lower:
                departments.update(dept_list)

        # 3. 中文分词增强匹配
        try:
            words = jieba.cut(symptom_lower)
            for word in words:
                if len(word) > 1:  # 只处理有意义的词
                    for keyword, dept_list in self.symptom_to_department.items():
                        if keyword in word:
                            departments.update(dept_list)
        except:
            pass  # 分词失败时降级

        return list(departments) if departments else ['全科']

    def _hierarchical_filter(self, vector_matches: List[tuple], departments: List[str], symptom: str) -> List[Dict]:
        """分层过滤医生"""
        filtered_doctors = []

        for doctor_idx, similarity in vector_matches:
            if doctor_idx < len(self.doctors):
                doctor = self.doctors[doctor_idx].copy()

                # 第一层：科室匹配
                if departments and doctor['specialty'] not in departments:
                    continue

                # 第二层：可用性检查
                if not doctor.get('available', True):
                    continue

                doctor['vector_similarity'] = similarity
                filtered_doctors.append(doctor)

        return filtered_doctors

    def _optimized_ranking(self, doctors: List[Dict], symptom: str) -> List[Dict]:
        """优化版排序算法"""
        ranked = []

        for doctor in doctors:
            score = self._calculate_comprehensive_score(doctor, symptom)
            doctor['match_score'] = min(round(score, 1), 100)
            ranked.append(doctor)

        # 按综合分数排序
        return sorted(ranked, key=lambda x: x['match_score'], reverse=True)

    def _calculate_comprehensive_score(self, doctor: Dict, symptom: str) -> float:
        """计算综合匹配分数"""
        score = 0.0

        # 1. 向量相似度（最重要）
        vector_sim = doctor.get('vector_similarity', 0)
        score += vector_sim * 40  # 40%权重

        # 2. 医生评分
        score += doctor['rating'] * 15  # 15%权重

        # 3. 经验权重（对数增长，避免过度影响）
        experience = doctor['experience']
        score += min(np.log(experience + 1) * 8, 20)  # 上限20分

        # 4. 距离权重（反比）
        distance = doctor['distance']
        score += (1 / (distance + 0.1)) * 12  # 12%权重

        # 5. 患者量权重（体现受欢迎程度）
        patient_volume = doctor.get('patient_volume', 0)
        score += min(patient_volume / 100, 10)  # 上限10分

        # 6. 职称权重
        title_bonus = {
            '主任医师': 8,
            '副主任医师': 6,
            '主治医师': 4,
            '医师': 2
        }
        score += title_bonus.get(doctor['title'], 0)

        return score

    def _get_ai_enhancement(self, symptom: str, top_doctors: List[Dict]) -> Dict:
        """获取AI增强分析"""
        try:
            doctor_info = "\n".join([
                f"{i + 1}. {doc['name']}医生 ({doc['specialty']}) - 匹配度: {doc['match_score']}%"
                for i, doc in enumerate(top_doctors)
            ])

            prompt = f"""
用户症状描述：{symptom}

推荐医生列表：
{doctor_info}

请基于以上信息，提供专业的医疗建议：
1. 症状可能对应的疾病方向
2. 推荐医生的专业匹配度分析
3. 就医前的注意事项
4. 是否需要紧急就医的判断

请用专业但易懂的中文回答。
"""

            ai_response = self.deepseek_rag.ask_question(prompt)

            return {
                'advice': ai_response,
                'analysis_time': time.time()
            }

        except Exception as e:
            logger.error(f"AI增强分析失败: {e}")
            return {
                'advice': 'AI分析服务暂时不可用',
                'error': str(e)
            }

    # 保持兼容性的旧接口
    def recommend_doctors_by_symptom(self, symptom: str, use_ai: bool = True) -> Dict:
        """兼容旧接口"""
        return self.recommend_doctors_optimized(symptom, use_ai)

    # 其他原有方法保持兼容
    def search_doctors_by_criteria(self, specialty: str = "", location: str = "", min_rating: float = 0) -> Dict:
        """按条件搜索医生（优化版）"""
        start_time = time.time()

        try:
            matched_doctors = []

            for doctor in self.doctors:
                match = True

                # 专科筛选
                if specialty and specialty != doctor.get('specialty', ''):
                    match = False

                # 地区筛选（模拟）
                if location and location not in doctor.get('hospital', ''):
                    match = False

                # 评分筛选
                if doctor.get('rating', 0) < min_rating:
                    match = False

                if match:
                    matched_doctors.append(doctor)

            processing_time = time.time() - start_time

            return {
                'success': True,
                'data': {
                    'doctors': matched_doctors,
                    'total': len(matched_doctors),
                    'processing_time': processing_time
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'搜索失败: {str(e)}'
            }

    def get_doctor_details(self, doctor_id: int) -> Dict:
        """获取医生详细信息"""
        try:
            for doctor in self.doctors:
                if doctor['id'] == doctor_id:
                    return {
                        'success': True,
                        'data': doctor
                    }

            return {
                'success': False,
                'message': '未找到该医生'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'获取详情失败: {str(e)}'
            }

    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return {
            'total_doctors': len(self.doctors),
            'vectorizer_ready': self.vectorizer is not None,
            'symptom_index_size': len(self.symptom_index),
            'optimization_enabled': True
        }


# 兼容性包装器
class DoctorRecommendationSystem(OptimizedDoctorRecommendationSystem):
    """兼容旧版本的包装类"""

    def __init__(self, retriever, deepseek_rag=None):
        super().__init__(retriever, deepseek_rag)


# 保持原有的全局函数，这是关键修复！
def get_langchain_service():
    """获取LangChain服务实例 - 保持与原有代码兼容"""
    global _langchain_service_instance
    if _langchain_service_instance is None:
        _langchain_service_instance = DoctorLangChainService()
    return _langchain_service_instance


# 添加缺失的类定义以保持兼容性
class DoctorLangChainService:
    """保持兼容性的LangChain服务类"""
    def __init__(self):
        logger.info("✓ 兼容性LangChain服务初始化")
        # 这里可以添加实际的LangChain服务逻辑
        pass

    async def ask_medical_question(self, question: str) -> Dict[str, Any]:
        """保持接口兼容性"""
        return {
            "success": True,
            "answer": "这是兼容性回答，请检查LangChain服务配置",
            "source": "compatibility"
        }


# 全局实例变量
_langchain_service_instance = None