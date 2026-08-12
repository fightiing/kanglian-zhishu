#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康档案管理模块
功能：管理用户健康档案，包括基本信息、病史、过敏史、用药记录、生理指标等
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class HealthRecordManager:
    """健康档案管理器"""
    
    def __init__(self, data_dir="health_records"):
        """
        初始化健康档案管理器
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def create_health_record(self, user_id, basic_info):
        """
        创建健康档案
        Args:
            user_id: 用户ID
            basic_info: 基本信息字典
        Returns:
            成功状态
        """
        try:
            # 检查用户ID是否已存在
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            if os.path.exists(file_path):
                print(f"用户ID已存在: {user_id}")
                return False
            
            record = {
                "user_id": user_id,
                "basic_info": basic_info,
                "medical_history": [],
                "allergies": [],
                "medications": [],
                "vital_signs": [],  # 生理指标记录
                "family_members": [],  # 家属信息
                "doctors": [],  # 医生信息
                "notifications": [],  # 通知记录
                "messages": [],  # 消息记录
                "access_tokens": [],  # 访问令牌
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"创建健康档案失败: {e}")
            return False
    
    def get_health_record(self, user_id):
        """
        获取健康档案
        Args:
            user_id: 用户ID
        Returns:
            健康档案字典
        """
        try:
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                record = json.load(f)
            
            return record
        except Exception as e:
            print(f"获取健康档案失败: {e}")
            return None
    
    def update_health_record(self, user_id, updates):
        """
        更新健康档案
        Args:
            user_id: 用户ID
            updates: 更新内容字典
        Returns:
            成功状态
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return False
            
            # 更新基本信息
            if "basic_info" in updates:
                record["basic_info"].update(updates["basic_info"])
            
            # 更新病史
            if "medical_history" in updates:
                record["medical_history"].extend(updates["medical_history"])
            
            # 更新过敏史
            if "allergies" in updates:
                record["allergies"].extend(updates["allergies"])
            
            # 更新用药记录
            if "medications" in updates:
                record["medications"].extend(updates["medications"])
            
            # 更新生理指标
            if "vital_signs" in updates:
                record["vital_signs"].extend(updates["vital_signs"])
            
            # 更新家属信息
            if "family_members" in updates:
                if "family_members" not in record:
                    record["family_members"] = []
                
                # 检查家属ID唯一性
                existing_ids = [member.get("id") for member in record["family_members"]]
                for member in updates["family_members"]:
                    member_id = member.get("id")
                    if not member_id:
                        print("家属ID不能为空")
                        return False
                    if member_id in existing_ids:
                        print(f"家属ID已存在: {member_id}")
                        return False
                    record["family_members"].append(member)
                    existing_ids.append(member_id)
            
            # 更新医生信息
            if "doctors" in updates:
                if "doctors" not in record:
                    record["doctors"] = []
                
                # 检查医生ID唯一性
                existing_ids = [doctor.get("id") for doctor in record["doctors"]]
                for doctor in updates["doctors"]:
                    doctor_id = doctor.get("id")
                    if not doctor_id:
                        print("医生ID不能为空")
                        return False
                    if doctor_id in existing_ids:
                        print(f"医生ID已存在: {doctor_id}")
                        return False
                    record["doctors"].append(doctor)
                    existing_ids.append(doctor_id)
            
            record["updated_at"] = datetime.now().isoformat()
            
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新健康档案失败: {e}")
            return False
    
    def add_vital_sign(self, user_id, vital_sign: Dict[str, Any]) -> bool:
        """
        添加生理指标记录
        Args:
            user_id: 用户ID
            vital_sign: 生理指标字典，包含：
                - type: 指标类型（blood_pressure/heart_rate/blood_sugar/temperature/weight/oxygen）
                - value: 测量值
                - secondary_value: 辅助值（如舒张压）
                - measured_at: 测量时间
                - notes: 备注
        Returns:
            成功状态
        """
        try:
            vital_sign["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"vital_signs": [vital_sign]})
        except Exception as e:
            print(f"添加生理指标失败: {e}")
            return False
    
    def get_vital_signs(self, user_id: str, vital_type: Optional[str] = None, 
                       days: int = 30) -> List[Dict[str, Any]]:
        """
        获取生理指标记录
        Args:
            user_id: 用户ID
            vital_type: 指标类型过滤（如不指定则返回所有）
            days: 获取最近天数（默认30天）
        Returns:
            生理指标列表
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return []
            
            vital_signs = record.get("vital_signs", [])
            
            # 按时间过滤
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_signs = []
            for sign in vital_signs:
                try:
                    measured_at = datetime.fromisoformat(sign.get("measured_at", sign.get("added_at", "")))
                    if measured_at >= cutoff_date:
                        if vital_type is None or sign.get("type") == vital_type:
                            filtered_signs.append(sign)
                except:
                    continue
            
            # 按时间排序（最新的在前）
            filtered_signs.sort(key=lambda x: x.get("measured_at", x.get("added_at", "")), reverse=True)
            
            return filtered_signs
        except Exception as e:
            print(f"获取生理指标失败: {e}")
            return []
    
    def analyze_vital_signs(self, user_id: str, vital_type: str) -> Dict[str, Any]:
        """
        分析生理指标趋势
        Args:
            user_id: 用户ID
            vital_type: 指标类型
        Returns:
            分析结果字典
        """
        try:
            signs = self.get_vital_signs(user_id, vital_type, days=30)
            if not signs:
                return {
                    "type": vital_type,
                    "count": 0,
                    "message": "暂无数据"
                }
            
            values = []
            for sign in signs:
                if vital_type == "blood_pressure":
                    values.append((sign.get("value", 0), sign.get("secondary_value", 0)))
                else:
                    values.append(sign.get("value", 0))
            
            if vital_type == "blood_pressure":
                systolic = [v[0] for v in values]
                diastolic = [v[1] for v in values]
                avg_systolic = sum(systolic) / len(systolic)
                avg_diastolic = sum(diastolic) / len(diastolic)
                
                # 判断血压状态
                latest = signs[0]
                systolic_val = latest.get("value", 0)
                diastolic_val = latest.get("secondary_value", 0)
                
                if systolic_val < 120 and diastolic_val < 80:
                    status = "正常"
                elif systolic_val < 130 and diastolic_val < 80:
                    status = "偏高"
                elif systolic_val < 140 or diastolic_val < 90:
                    status = "高血压前期"
                else:
                    status = "高血压"
                
                return {
                    "type": vital_type,
                    "count": len(signs),
                    "period": "近30天",
                    "average": {
                        "systolic": round(avg_systolic, 1),
                        "diastolic": round(avg_diastolic, 1)
                    },
                    "latest": {
                        "systolic": systolic_val,
                        "diastolic": diastolic_val,
                        "measured_at": latest.get("measured_at", latest.get("added_at", ""))
                    },
                    "status": status,
                    "trend": "stable" if abs(systolic[-1] - systolic[0]) < 10 else ("up" if systolic[-1] > systolic[0] else "down")
                }
            elif vital_type == "heart_rate":
                avg_rate = sum(values) / len(values)
                latest = signs[0]
                rate_val = latest.get("value", 0)
                
                if rate_val < 60:
                    status = "偏低"
                elif rate_val <= 100:
                    status = "正常"
                else:
                    status = "偏高"
                
                return {
                    "type": vital_type,
                    "count": len(signs),
                    "period": "近30天",
                    "average": round(avg_rate, 1),
                    "latest": {
                        "value": rate_val,
                        "measured_at": latest.get("measured_at", latest.get("added_at", ""))
                    },
                    "status": status,
                    "trend": "stable" if abs(values[-1] - values[0]) < 10 else ("up" if values[-1] > values[0] else "down")
                }
            elif vital_type == "blood_sugar":
                avg_sugar = sum(values) / len(values)
                latest = signs[0]
                sugar_val = latest.get("value", 0)
                
                if sugar_val < 3.9:
                    status = "偏低"
                elif sugar_val <= 6.1:
                    status = "正常"
                elif sugar_val <= 7.0:
                    status = "偏高（糖尿病前期）"
                else:
                    status = "高血糖"
                
                return {
                    "type": vital_type,
                    "count": len(signs),
                    "period": "近30天",
                    "average": round(avg_sugar, 2),
                    "latest": {
                        "value": sugar_val,
                        "measured_at": latest.get("measured_at", latest.get("added_at", ""))
                    },
                    "status": status,
                    "trend": "stable" if abs(values[-1] - values[0]) < 2 else ("up" if values[-1] > values[0] else "down")
                }
            else:
                avg_val = sum(values) / len(values)
                latest = signs[0]
                
                return {
                    "type": vital_type,
                    "count": len(signs),
                    "period": "近30天",
                    "average": round(avg_val, 1),
                    "latest": {
                        "value": latest.get("value", 0),
                        "measured_at": latest.get("measured_at", latest.get("added_at", ""))
                    },
                    "trend": "stable"
                }
        except Exception as e:
            print(f"分析生理指标失败: {e}")
            return {"error": str(e)}
    
    def get_health_summary(self, user_id: str) -> Dict[str, Any]:
        """
        获取健康摘要
        Args:
            user_id: 用户ID
        Returns:
            健康摘要字典
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return {"error": "用户不存在"}
            
            basic_info = record.get("basic_info", {})
            vital_signs = record.get("vital_signs", [])
            medications = record.get("medications", [])
            
            # 统计各类指标数量
            bp_count = len([v for v in vital_signs if v.get("type") == "blood_pressure"])
            hr_count = len([v for v in vital_signs if v.get("type") == "heart_rate"])
            bs_count = len([v for v in vital_signs if v.get("type") == "blood_sugar"])
            
            # 生成风险预警
            risk_alert = self.generate_risk_alert(user_id)
            
            return {
                "user_id": user_id,
                "basic_info": {
                    "name": basic_info.get("name", ""),
                    "age": basic_info.get("age", ""),
                    "gender": basic_info.get("gender", "")
                },
                "statistics": {
                    "total_vital_signs": len(vital_signs),
                    "blood_pressure_records": bp_count,
                    "heart_rate_records": hr_count,
                    "blood_sugar_records": bs_count,
                    "medications": len(medications)
                },
                "recent_status": {
                    "blood_pressure": self.analyze_vital_signs(user_id, "blood_pressure") if bp_count > 0 else None,
                    "heart_rate": self.analyze_vital_signs(user_id, "heart_rate") if hr_count > 0 else None,
                    "blood_sugar": self.analyze_vital_signs(user_id, "blood_sugar") if bs_count > 0 else None
                },
                "risk_alert": risk_alert
            }
        except Exception as e:
            print(f"获取健康摘要失败: {e}")
            return {"error": str(e)}
    
    def generate_risk_alert(self, user_id: str) -> Dict[str, Any]:
        """
        生成健康风险预警
        Args:
            user_id: 用户ID
        Returns:
            风险预警字典
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return {"level": "none", "message": "无数据"}
            
            alerts = []
            risk_level = "normal"
            
            # 分析血压
            bp_analysis = self.analyze_vital_signs(user_id, "blood_pressure")
            if bp_analysis and "status" in bp_analysis:
                if bp_analysis["status"] == "高血压":
                    alerts.append("血压偏高，建议及时就医")
                    risk_level = "high" if risk_level != "high" else risk_level
                elif bp_analysis["status"] == "高血压前期":
                    alerts.append("血压处于临界值，建议注意监测")
                    risk_level = "medium" if risk_level != "high" else risk_level
            
            # 分析心率
            hr_analysis = self.analyze_vital_signs(user_id, "heart_rate")
            if hr_analysis and "status" in hr_analysis:
                if hr_analysis["status"] == "偏高" and hr_analysis.get("latest", {}).get("value", 0) > 120:
                    alerts.append("心率过高，建议休息并监测")
                    risk_level = "high" if risk_level != "high" else risk_level
                elif hr_analysis["status"] == "偏低" and hr_analysis.get("latest", {}).get("value", 0) < 50:
                    alerts.append("心率过低，建议就医检查")
                    risk_level = "high" if risk_level != "high" else risk_level
            
            # 分析血糖
            bs_analysis = self.analyze_vital_signs(user_id, "blood_sugar")
            if bs_analysis and "status" in bs_analysis:
                if bs_analysis["status"] == "高血糖":
                    alerts.append("血糖偏高，建议控制饮食并监测")
                    risk_level = "high" if risk_level != "high" else risk_level
                elif bs_analysis["status"] == "偏高（糖尿病前期）":
                    alerts.append("血糖处于临界值，建议调整生活方式")
                    risk_level = "medium" if risk_level != "high" else risk_level
            
            # 分析用药依从性
            medications = record.get("medications", [])
            if medications:
                recent_meds = [m for m in medications if datetime.fromisoformat(m.get("added_at", "2000-01-01T00:00:00")) > datetime.now() - timedelta(days=7)]
                if len(recent_meds) < len(medications) * 0.7:
                    alerts.append("用药记录不完整，建议按时服药")
                    risk_level = "medium" if risk_level != "high" else risk_level
            
            # 生成预警消息
            if not alerts:
                return {
                    "level": "normal",
                    "message": "健康状态良好",
                    "details": []
                }
            else:
                return {
                    "level": risk_level,
                    "message": self._get_risk_message(risk_level),
                    "details": alerts
                }
        except Exception as e:
            print(f"生成风险预警失败: {e}")
            return {"level": "none", "message": "无法生成预警"}
    
    def _get_risk_message(self, level: str) -> str:
        """
        根据风险等级获取预警消息
        Args:
            level: 风险等级
        Returns:
            预警消息
        """
        messages = {
            "high": "⚠️ 健康风险较高，建议立即就医",
            "medium": "⚠️ 健康风险中等，建议密切监测",
            "normal": "✅ 健康状态良好",
            "none": "无数据"
        }
        return messages.get(level, "无数据")
    
    def generate_health_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        生成个性化健康建议
        Args:
            user_id: 用户ID
        Returns:
            健康建议字典
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return {"error": "用户不存在"}
            
            recommendations = []
            
            # 分析血压
            bp_analysis = self.analyze_vital_signs(user_id, "blood_pressure")
            if bp_analysis and "status" in bp_analysis:
                if bp_analysis["status"] == "高血压":
                    recommendations.append({
                        "type": "blood_pressure",
                        "title": "血压管理建议",
                        "content": "1. 减少盐分摄入，每日盐摄入量不超过5克\n2. 保持规律运动，如散步、太极拳等\n3. 定期监测血压，每天至少测量2次\n4. 按医嘱服用降压药物，不可自行停药\n5. 保持充足睡眠，避免情绪激动"
                    })
                elif bp_analysis["status"] == "高血压前期":
                    recommendations.append({
                        "type": "blood_pressure",
                        "title": "血压管理建议",
                        "content": "1. 调整饮食结构，增加蔬菜水果摄入\n2. 适当增加运动量，每周至少150分钟\n3. 定期监测血压变化\n4. 保持健康体重，避免肥胖"
                    })
            
            # 分析血糖
            bs_analysis = self.analyze_vital_signs(user_id, "blood_sugar")
            if bs_analysis and "status" in bs_analysis:
                if bs_analysis["status"] == "高血糖":
                    recommendations.append({
                        "type": "blood_sugar",
                        "title": "血糖管理建议",
                        "content": "1. 控制碳水化合物摄入，选择低GI食物\n2. 规律饮食，定时定量\n3. 适当运动，如散步、游泳等\n4. 按医嘱服用降糖药物\n5. 定期监测血糖变化"
                    })
                elif bs_analysis["status"] == "偏高（糖尿病前期）":
                    recommendations.append({
                        "type": "blood_sugar",
                        "title": "血糖管理建议",
                        "content": "1. 调整饮食结构，减少精制碳水摄入\n2. 增加膳食纤维摄入\n3. 保持规律运动\n4. 定期监测血糖变化"
                    })
            
            # 分析心率
            hr_analysis = self.analyze_vital_signs(user_id, "heart_rate")
            if hr_analysis and "status" in hr_analysis:
                if hr_analysis["status"] == "偏高":
                    recommendations.append({
                        "type": "heart_rate",
                        "title": "心率管理建议",
                        "content": "1. 避免过度劳累和情绪激动\n2. 保持充足睡眠\n3. 适当进行放松训练，如深呼吸、冥想\n4. 避免饮用咖啡、浓茶等刺激性饮料"
                    })
                elif hr_analysis["status"] == "偏低":
                    recommendations.append({
                        "type": "heart_rate",
                        "title": "心率管理建议",
                        "content": "1. 避免突然改变体位\n2. 适当增加运动量，增强心肺功能\n3. 保持均衡饮食，避免营养不良"
                    })
            
            # 用药依从性建议
            medications = record.get("medications", [])
            if medications:
                recommendations.append({
                    "type": "medication",
                    "title": "用药建议",
                    "content": "1. 按时服药，不要自行增减药量\n2. 了解药物的作用和副作用\n3. 定期复查，根据医生建议调整用药方案\n4. 如有不适，及时咨询医生"
                })
            
            # 通用健康建议
            recommendations.append({
                "type": "general",
                "title": "日常健康建议",
                "content": "1. 保持规律作息，保证充足睡眠\n2. 均衡饮食，多吃蔬菜水果\n3. 适当运动，保持身体健康\n4. 保持积极乐观的心态\n5. 定期体检，及时发现健康问题"
            })
            
            return {
                "success": True,
                "recommendations": recommendations
            }
        except Exception as e:
            print(f"生成健康建议失败: {e}")
            return {"error": str(e)}
    
    def add_medication(self, user_id, medication):
        """
        添加用药记录
        Args:
            user_id: 用户ID
            medication: 用药信息字典
        Returns:
            成功状态
        """
        try:
            medication["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"medications": [medication]})
        except Exception as e:
            print(f"添加用药记录失败: {e}")
            return False
    
    def add_medical_history(self, user_id, medical_record):
        """
        添加病史记录
        Args:
            user_id: 用户ID
            medical_record: 病史信息字典
        Returns:
            成功状态
        """
        try:
            medical_record["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"medical_history": [medical_record]})
        except Exception as e:
            print(f"添加病史记录失败: {e}")
            return False
    
    def add_allergy(self, user_id, allergy):
        """
        添加过敏史记录
        Args:
            user_id: 用户ID
            allergy: 过敏信息字典
        Returns:
            成功状态
        """
        try:
            allergy["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"allergies": [allergy]})
        except Exception as e:
            print(f"添加过敏史记录失败: {e}")
            return False
    
    def add_family_member(self, user_id, family_member):
        """
        添加家属信息
        Args:
            user_id: 用户ID
            family_member: 家属信息字典，包含：
                - name: 姓名
                - relationship: 关系
                - phone: 电话
                - email: 邮箱
                - can_view: 是否可以查看健康档案
                - can_edit: 是否可以编辑健康档案
        Returns:
            成功状态
        """
        try:
            # 添加唯一ID
            family_member["id"] = family_member.get("phone")  # 使用电话作为ID
            family_member["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"family_members": [family_member]})
        except Exception as e:
            print(f"添加家属信息失败: {e}")
            return False
    
    def add_doctor(self, user_id, doctor):
        """
        添加医生信息
        Args:
            user_id: 用户ID
            doctor: 医生信息字典，包含：
                - name: 姓名
                - department: 科室
                - hospital: 医院
                - phone: 电话
                - can_view: 是否可以查看健康档案
                - can_edit: 是否可以编辑健康档案
        Returns:
            成功状态
        """
        try:
            # 添加唯一ID
            doctor["id"] = doctor.get("phone")  # 使用电话作为ID
            doctor["added_at"] = datetime.now().isoformat()
            return self.update_health_record(user_id, {"doctors": [doctor]})
        except Exception as e:
            print(f"添加医生信息失败: {e}")
            return False
    
    def generate_access_link(self, user_id, viewer_id, viewer_type):
        """
        生成专属访问链接
        Args:
            user_id: 用户ID
            viewer_id: 查看者ID
            viewer_type: 查看者类型（family/doctor）
        Returns:
            专属访问链接
        """
        try:
            import hashlib
            import time
            
            # 生成唯一标识
            timestamp = str(int(time.time()))
            data = f"{user_id}_{viewer_id}_{viewer_type}_{timestamp}"
            token = hashlib.md5(data.encode()).hexdigest()
            
            # 生成访问链接
            base_url = "http://localhost:8080/health_record/shared"
            access_link = f"{base_url}?user_id={user_id}&viewer_id={viewer_id}&viewer_type={viewer_type}&token={token}"
            
            # 保存token到健康档案
            record = self.get_health_record(user_id)
            if record:
                # 确保token存储结构存在
                if "access_tokens" not in record:
                    record["access_tokens"] = []
                
                # 添加新token
                record["access_tokens"].append({
                    "token": token,
                    "viewer_id": viewer_id,
                    "viewer_type": viewer_type,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=365)).isoformat()  # 有效期1年
                })
                
                # 保存更新后的记录
                file_path = os.path.join(self.data_dir, f"{user_id}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
            
            return access_link
        except Exception as e:
            print(f"生成访问链接失败: {e}")
            return None
    
    def verify_access_token(self, user_id, token):
        """
        验证访问token
        Args:
            user_id: 用户ID
            token: 访问token
        Returns:
            验证结果和查看者信息
        """
        try:
            record = self.get_health_record(user_id)
            if not record or "access_tokens" not in record:
                return {"valid": False, "message": "无效的访问链接"}
            
            # 查找token
            for token_info in record["access_tokens"]:
                if token_info["token"] == token:
                    # 检查是否过期
                    expires_at = datetime.fromisoformat(token_info["expires_at"])
                    if datetime.now() > expires_at:
                        return {"valid": False, "message": "访问链接已过期"}
                    
                    return {
                        "valid": True,
                        "viewer_id": token_info["viewer_id"],
                        "viewer_type": token_info["viewer_type"]
                    }
            
            return {"valid": False, "message": "无效的访问链接"}
        except Exception as e:
            print(f"验证访问token失败: {e}")
            return {"valid": False, "message": "验证失败"}
    
    def get_shared_health_record(self, user_id, viewer_id, viewer_type):
        """
        获取共享的健康档案（根据权限）
        Args:
            user_id: 用户ID
            viewer_id: 查看者ID
            viewer_type: 查看者类型（family/doctor）
        Returns:
            健康档案字典（根据权限过滤）
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return None
            
            # 检查权限
            can_view = False
            can_edit = False
            
            print(f"检查权限: viewer_id={viewer_id}, viewer_type={viewer_type}")
            print(f"家属列表: {record.get('family_members', [])}")
            print(f"医生列表: {record.get('doctors', [])}")
            
            if viewer_type == "family":
                for member in record.get("family_members", []):
                    print(f"检查家属: id={member.get('id')}, phone={member.get('phone')}, can_view={member.get('can_view')}")
                    if member.get("id") == viewer_id or member.get("phone") == viewer_id:
                        can_view = member.get("can_view", False)
                        can_edit = member.get("can_edit", False)
                        print(f"找到家属: can_view={can_view}")
                        break
            elif viewer_type == "doctor":
                for doc in record.get("doctors", []):
                    print(f"检查医生: id={doc.get('id')}, phone={doc.get('phone')}, can_view={doc.get('can_view')}")
                    if doc.get("id") == viewer_id or doc.get("phone") == viewer_id:
                        can_view = doc.get("can_view", False)
                        can_edit = doc.get("can_edit", False)
                        print(f"找到医生: can_view={can_view}")
                        break
            
            if not can_view:
                return {"error": "无查看权限"}
            
            # 根据权限返回相应数据
            if can_edit:
                return record
            else:
                # 只读权限，返回部分数据
                return {
                    "user_id": record.get("user_id"),
                    "basic_info": record.get("basic_info"),
                    "medical_history": record.get("medical_history"),
                    "allergies": record.get("allergies"),
                    "medications": record.get("medications"),
                    "vital_signs": record.get("vital_signs"),
                    "risk_alert": self.generate_risk_alert(user_id),
                    "recommendations": self.generate_health_recommendations(user_id)
                }
        except Exception as e:
            print(f"获取共享健康档案失败: {e}")
            return {"error": str(e)}
    
    def add_notification(self, user_id, title, content, notification_type="info", recipients=None):
        """
        添加通知
        Args:
            user_id: 用户ID
            title: 通知标题
            content: 通知内容
            notification_type: 通知类型 (info, warning, error, success)
            recipients: 接收者列表 [{"id": "接收者ID", "type": "family/doctor"}]
        Returns:
            True if success, False otherwise
        """
        try:
            print("=== 开始添加通知 ===")
            print(f"user_id: {user_id}")
            print(f"title: {title}")
            print(f"content: {content}")
            print(f"notification_type: {notification_type}")
            print(f"recipients: {recipients}")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"数据目录: {self.data_dir}")
            
            # 使用self.data_dir构建文件路径
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            print(f"文件路径: {file_path}")
            print(f"文件存在: {os.path.exists(file_path)}")
            
            # 读取健康档案
            if not os.path.exists(file_path):
                print(f"健康档案文件不存在: {file_path}")
                return False
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                print("读取健康档案成功")
                print(f"健康档案内容: {record}")
            except Exception as e:
                print(f"读取健康档案失败: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # 确保通知存储结构存在
            if "notifications" not in record:
                record["notifications"] = []
                print("创建notifications字段")
            
            # 创建通知
            notification = {
                "id": str(int(time.time())),
                "title": title,
                "content": content,
                "type": notification_type,
                "created_at": datetime.now().isoformat(),
                "read": False,
                "recipients": recipients or []
            }
            print(f"创建通知: {notification}")
            
            # 添加通知
            record["notifications"].append(notification)
            print(f"通知添加到列表: {len(record['notifications'])} 条通知")
            
            # 保存更新后的记录
            print(f"保存文件: {file_path}")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
                print("文件保存成功")
            except Exception as e:
                print(f"文件保存失败: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            print("=== 通知添加成功 ===")
            return True
        except Exception as e:
            print(f"添加通知失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_notifications(self, user_id, viewer_id=None, viewer_type=None):
        """
        获取通知
        Args:
            user_id: 用户ID
            viewer_id: 查看者ID（可选，用于筛选接收者）
            viewer_type: 查看者类型（可选，用于筛选接收者）
        Returns:
            通知列表
        """
        try:
            record = self.get_health_record(user_id)
            if not record or "notifications" not in record:
                return []
            
            notifications = record["notifications"]
            
            # 如果指定了查看者，筛选该查看者的通知
            if viewer_id and viewer_type:
                filtered_notifications = []
                for notification in notifications:
                    # 检查是否是发给该查看者的通知
                    recipients = notification.get("recipients", [])
                    for recipient in recipients:
                        if recipient.get("id") == viewer_id and recipient.get("type") == viewer_type:
                            filtered_notifications.append(notification)
                            break
                return filtered_notifications
            
            return notifications
        except Exception as e:
            print(f"获取通知失败: {e}")
            return []
    
    def mark_notification_read(self, user_id, notification_id):
        """
        标记通知为已读
        Args:
            user_id: 用户ID
            notification_id: 通知ID
        Returns:
            True if success, False otherwise
        """
        try:
            record = self.get_health_record(user_id)
            if not record or "notifications" not in record:
                return False
            
            # 查找并标记通知
            for notification in record["notifications"]:
                if notification.get("id") == notification_id:
                    notification["read"] = True
                    break
            
            # 保存更新后的记录
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"标记通知已读失败: {e}")
            return False
    
    def add_message(self, user_id, sender_id, sender_type, content, message_type="text"):
        """
        添加消息（用于多方沟通）
        Args:
            user_id: 用户ID
            sender_id: 发送者ID
            sender_type: 发送者类型 (family/doctor)
            content: 消息内容
            message_type: 消息类型 (text, image, file)
        Returns:
            True if success, False otherwise
        """
        try:
            record = self.get_health_record(user_id)
            if not record:
                return False
            
            # 确保消息存储结构存在
            if "messages" not in record:
                record["messages"] = []
            
            # 创建消息
            message = {
                "id": str(int(time.time())),
                "sender_id": sender_id,
                "sender_type": sender_type,
                "content": content,
                "type": message_type,
                "created_at": datetime.now().isoformat(),
                "read": False
            }
            
            # 添加消息
            record["messages"].append(message)
            
            # 保存更新后的记录
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"添加消息失败: {e}")
            return False
    
    def get_messages(self, user_id):
        """
        获取消息列表
        Args:
            user_id: 用户ID
        Returns:
            消息列表
        """
        try:
            record = self.get_health_record(user_id)
            if not record or "messages" not in record:
                return []
            
            # 按时间排序
            messages = record["messages"]
            messages.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return messages
        except Exception as e:
            print(f"获取消息失败: {e}")
            return []
    
    def mark_message_read(self, user_id, message_id):
        """
        标记消息为已读
        Args:
            user_id: 用户ID
            message_id: 消息ID
        Returns:
            True if success, False otherwise
        """
        try:
            record = self.get_health_record(user_id)
            if not record or "messages" not in record:
                return False
            
            # 查找并标记消息
            for message in record["messages"]:
                if message.get("id") == message_id:
                    message["read"] = True
                    break
            
            # 保存更新后的记录
            file_path = os.path.join(self.data_dir, f"{user_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"标记消息已读失败: {e}")
            return False
    
    def list_users(self):
        """
        列出所有用户
        Returns:
            用户ID列表
        """
        try:
            users = []
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    user_id = filename[:-5]  # 移除.json后缀
                    users.append(user_id)
            return users
        except Exception as e:
            print(f"列出用户失败: {e}")
            return []