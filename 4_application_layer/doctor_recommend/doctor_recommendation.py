#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
医生推荐系统 - 增强版
支持知识图谱匹配 + AI分析
"""

import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class DoctorRecommendationSystem:
    """医生推荐系统 - 增强版"""

    def __init__(self, retriever, deepseek_rag=None):
        """
        初始化医生推荐系统

        Args:
            retriever: 医学知识图谱检索器
            deepseek_rag: DeepSeek RAG服务（可选）
        """
        self.retriever = retriever
        self.deepseek_rag = deepseek_rag

        # 模拟医生数据库
        self.doctors = self._init_doctor_database()

        # 症状关键词到科室的映射
        self.symptom_to_department = {
            '心血管': ['心内科', '心血管内科', '心外科'],
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
            '乏力': ['全科', '神经内科', '内分泌科']
        }

        logger.info("✓ 医生推荐系统初始化完成")

    def _init_doctor_database(self) -> List[Dict]:
        """初始化模拟医生数据库"""
        return [
            {
                'id': 1,
                'name': '王明德',
                'title': '主任医师',
                'specialty': '心内科',
                'hospital': '北京协和医院',
                'experience': 20,
                'rating': 4.8,
                'distance': 1.2,
                'schedule': '周一至周五 上午8:00-12:00',
                'expertise': ['冠心病', '高血压', '心力衰竭'],
                'available': True
            },
            {
                'id': 2,
                'name': '李华',
                'title': '副主任医师',
                'specialty': '心血管内科',
                'hospital': '北京大学人民医院',
                'experience': 15,
                'rating': 4.7,
                'distance': 2.5,
                'schedule': '周二至周六 下午14:00-17:00',
                'expertise': ['心律失常', '心肌病', '心脏康复'],
                'available': True
            },
            {
                'id': 3,
                'name': '张伟',
                'title': '主治医师',
                'specialty': '全科',
                'hospital': '朝阳社区卫生服务中心',
                'experience': 8,
                'rating': 4.5,
                'distance': 0.8,
                'schedule': '周一至周日 全天',
                'expertise': ['常见病', '慢病管理', '健康咨询'],
                'available': True
            },
            {
                'id': 4,
                'name': '陈静',
                'title': '主任医师',
                'specialty': '神经内科',
                'hospital': '北京天坛医院',
                'experience': 18,
                'rating': 4.9,
                'distance': 3.2,
                'schedule': '周一、周三、周五 上午',
                'expertise': ['中风', '帕金森', '头痛'],
                'available': True
            },
            {
                'id': 5,
                'name': '刘强',
                'title': '副主任医师',
                'specialty': '呼吸内科',
                'hospital': '北京中日友好医院',
                'experience': 12,
                'rating': 4.6,
                'distance': 1.8,
                'schedule': '周二、周四、周六 全天',
                'expertise': ['肺炎', '哮喘', '慢阻肺'],
                'available': True
            },
            {
                'id': 6,
                'name': '赵敏',
                'title': '主任医师',
                'specialty': '内分泌科',
                'hospital': '北京医院',
                'experience': 22,
                'rating': 4.8,
                'distance': 2.1,
                'schedule': '周一至周四 全天',
                'expertise': ['糖尿病', '甲状腺疾病', '骨质疏松'],
                'available': True
            },
            {
                'id': 7,
                'name': '孙建国',
                'title': '副主任医师',
                'specialty': '消化内科',
                'hospital': '北京友谊医院',
                'experience': 16,
                'rating': 4.7,
                'distance': 1.5,
                'schedule': '周一至周五 下午',
                'expertise': ['胃炎', '溃疡', '肝病'],
                'available': True
            },
            {
                'id': 8,
                'name': '周小红',
                'title': '主治医师',
                'specialty': '中医科',
                'hospital': '东直门社区卫生服务中心',
                'experience': 10,
                'rating': 4.4,
                'distance': 0.5,
                'schedule': '周一至周六 上午',
                'expertise': ['中医调理', '针灸', '推拿'],
                'available': True
            }
        ]

    def match_symptom_to_departments(self, symptom: str) -> List[str]:
        """
        将症状匹配到科室

        Args:
            symptom: 症状描述

        Returns:
            推荐的科室列表
        """
        recommended_departments = []

        # 1. 从知识图谱中查找相关疾病
        try:
            # 通过症状查找相关疾病
            disease_query = """
            MATCH (s:症状)-[:has_symptom]->(d:疾病)
            WHERE toLower(s.name) CONTAINS toLower($keyword)
            RETURN DISTINCT d.name as disease
            LIMIT 5
            """
            diseases = self.retriever.graph.run(disease_query, keyword=symptom).data()

            for record in diseases:
                disease_name = record['disease']
                # 获取疾病的就诊科室
                department_query = """
                MATCH (d:疾病 {name: $disease_name})-[:common_department]->(dept:科室)
                RETURN dept.name as department
                """
                departments = self.retriever.graph.run(department_query, disease_name=disease_name).data()
                for dept in departments:
                    if dept['department'] not in recommended_departments:
                        recommended_departments.append(dept['department'])
        except Exception as e:
            logger.warning(f"从知识图谱匹配科室失败: {e}")

        # 2. 通过关键词匹配
        symptom_lower = symptom.lower()
        for keyword, departments in self.symptom_to_department.items():
            if keyword in symptom_lower:
                for dept in departments:
                    if dept not in recommended_departments:
                        recommended_departments.append(dept)

        # 3. 如果没有匹配到，返回默认科室
        if not recommended_departments:
            recommended_departments = ['全科', '内科']

        return recommended_departments

    def analyze_symptoms_with_ai(self, symptom: str) -> str:
        """
        使用AI分析症状并推荐科室

        Args:
            symptom: 症状描述

        Returns:
            AI分析结果
        """
        if not self.deepseek_rag:
            return "AI分析服务暂不可用"

        try:
            prompt = f"""
用户描述的症状：{symptom}

请作为医疗专家，提供专业的分析建议：
1. 可能的疾病方向
2. 应该就诊的科室
3. 紧急程度评估
4. 就医前注意事项

请用中文专业、友好、易懂地回复，不要使用医学专业术语。
"""
            return self.deepseek_rag.ask_question(prompt)
        except Exception as e:
            logger.error(f"AI分析症状失败: {e}")
            return f"AI分析服务暂时不可用: {str(e)}"

    def recommend_doctors_by_symptom(self, symptom: str, use_ai: bool = True) -> Dict:
        """
        基于症状推荐医生

        Args:
            symptom: 症状描述
            use_ai: 是否使用AI增强分析

        Returns:
            推荐结果
        """
        try:
            # 1. 匹配科室
            recommended_departments = self.match_symptom_to_departments(symptom)

            # 2. 基于科室筛选医生
            matched_doctors = []
            for doctor in self.doctors:
                if doctor['specialty'] in recommended_departments:
                    # 计算匹配分数
                    score = self._calculate_match_score(doctor, symptom)
                    doctor_copy = doctor.copy()
                    doctor_copy['match_score'] = score
                    matched_doctors.append(doctor_copy)

            # 3. 排序（按匹配分数和评分）
            matched_doctors.sort(key=lambda x: (x['match_score'], x['rating']), reverse=True)

            # 4. AI增强分析
            ai_advice = None
            if use_ai and self.deepseek_rag:
                ai_advice = self.analyze_symptoms_with_ai(symptom)

            # 5. 获取相关的疾病
            matched_diseases = self._get_related_diseases(symptom)

            return {
                'success': True,
                'data': {
                    'symptom': symptom,
                    'matched_diseases': matched_diseases,
                    'recommended_departments': recommended_departments,
                    'doctors': matched_doctors[:5],  # 返回前5个
                    'ai_enhancement': {
                        'enabled': use_ai,
                        'advice': ai_advice
                    } if use_ai else None
                }
            }

        except Exception as e:
            logger.error(f"推荐医生失败: {e}")
            return {
                'success': False,
                'message': f'推荐失败: {str(e)}',
                'data': {
                    'symptom': symptom,
                    'doctors': []
                }
            }

    def _calculate_match_score(self, doctor: Dict, symptom: str) -> float:
        """
        计算医生与症状的匹配分数
        """
        score = 0.0

        # 基础分数
        score += doctor['rating'] * 2
        score += min(doctor['experience'] * 0.5, 10)  # 经验加分
        score += (1 / (doctor['distance'] + 0.1)) * 2  # 距离加分

        # 症状关键词匹配
        symptom_lower = symptom.lower()
        for keyword in self.symptom_to_department:
            if keyword in symptom_lower:
                for expertise in doctor.get('expertise', []):
                    if keyword in expertise.lower():
                        score += 5
                        break

        return round(score, 1)

    def _get_related_diseases(self, symptom: str) -> List[str]:
        """
        从知识图谱获取相关疾病
        """
        try:
            query = """
            MATCH (s:症状)-[:has_symptom]->(d:疾病)
            WHERE toLower(s.name) CONTAINS toLower($keyword)
            RETURN DISTINCT d.name as disease
            LIMIT 3
            """
            result = self.retriever.graph.run(query, keyword=symptom).data()
            return [r['disease'] for r in result]
        except Exception as e:
            logger.error(f"获取相关疾病失败: {e}")
            return []

    def search_doctors_by_criteria(self, specialty: str = "", location: str = "", min_rating: float = 0) -> Dict:
        """
        按条件搜索医生
        """
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

            return {
                'success': True,
                'data': {
                    'doctors': matched_doctors,
                    'total': len(matched_doctors)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'搜索失败: {str(e)}'
            }

    def get_doctor_details(self, doctor_id: int) -> Dict:
        """
        获取医生详细信息
        """
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

    def get_multi_disease_conflicts(self, diseases):
        """获取多疾病冲突信息"""
        try:
            if len(diseases) < 2:
                return []

            # 调用现有的冲突检测
            conflict_result = self.retriever.check_food_conflict(diseases)
            return conflict_result.get('饮食冲突', [])
        except Exception as e:
            logger.error(f"获取多疾病冲突失败: {e}")
            return []
