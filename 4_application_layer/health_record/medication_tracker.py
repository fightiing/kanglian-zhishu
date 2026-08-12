#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用药依从性跟踪模块
功能：设置用药提醒，跟踪用药记录，生成依从性报告
"""

import json
import os
from datetime import datetime, timedelta


class MedicationTracker:
    """用药依从性跟踪器"""
    
    def __init__(self, data_dir="medication_tracking"):
        """
        初始化用药跟踪器
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def set_medication_reminder(self, user_id, medication_info):
        """
        设置用药提醒
        Args:
            user_id: 用户ID
            medication_info: 用药信息字典
        Returns:
            提醒ID
        """
        try:
            # 确保用户目录存在
            user_dir = os.path.join(self.data_dir, user_id)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            # 生成提醒ID
            reminder_id = f"reminder_{datetime.now().timestamp()}"
            
            # 构建提醒信息
            reminder = {
                "reminder_id": reminder_id,
                "medication_name": medication_info.get("medication_name"),
                "dosage": medication_info.get("dosage"),
                "frequency": medication_info.get("frequency"),  # 如"每日3次"
                "times": medication_info.get("times", []),  # 具体时间列表，如["08:00", "12:00", "18:00"]
                "start_date": medication_info.get("start_date", datetime.now().isoformat()),
                "end_date": medication_info.get("end_date"),
                "notes": medication_info.get("notes", ""),
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # 保存提醒
            file_path = os.path.join(user_dir, f"{reminder_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(reminder, f, ensure_ascii=False, indent=2)
            
            return reminder_id
        except Exception as e:
            print(f"设置用药提醒失败: {e}")
            return None
    
    def record_medication(self, user_id, reminder_id, status="taken", notes=""):
        """
        记录用药情况
        Args:
            user_id: 用户ID
            reminder_id: 提醒ID
            status: 状态（taken, missed, skipped）
            notes: 备注
        Returns:
            成功状态
        """
        try:
            # 确保记录目录存在
            record_dir = os.path.join(self.data_dir, user_id, "records")
            if not os.path.exists(record_dir):
                os.makedirs(record_dir)
            
            # 构建记录
            record = {
                "user_id": user_id,
                "reminder_id": reminder_id,
                "status": status,
                "notes": notes,
                "recorded_at": datetime.now().isoformat()
            }
            
            # 保存记录
            record_id = f"record_{datetime.now().timestamp()}"
            file_path = os.path.join(record_dir, f"{record_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"记录用药情况失败: {e}")
            return False
    
    def get_user_reminders(self, user_id):
        """
        获取用户的所有提醒
        Args:
            user_id: 用户ID
        Returns:
            提醒列表
        """
        try:
            user_dir = os.path.join(self.data_dir, user_id)
            if not os.path.exists(user_dir):
                return []
            
            reminders = []
            for filename in os.listdir(user_dir):
                if filename.startswith("reminder_") and filename.endswith('.json'):
                    file_path = os.path.join(user_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reminder = json.load(f)
                    reminders.append(reminder)
            
            return reminders
        except Exception as e:
            print(f"获取用户提醒失败: {e}")
            return []
    
    def get_user_records(self, user_id, start_date=None, end_date=None):
        """
        获取用户的用药记录
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            记录列表
        """
        try:
            record_dir = os.path.join(self.data_dir, user_id, "records")
            if not os.path.exists(record_dir):
                return []
            
            records = []
            for filename in os.listdir(record_dir):
                if filename.startswith("record_") and filename.endswith('.json'):
                    file_path = os.path.join(record_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                    
                    # 过滤日期
                    recorded_at = datetime.fromisoformat(record["recorded_at"])
                    if start_date and recorded_at < start_date:
                        continue
                    if end_date and recorded_at > end_date:
                        continue
                    
                    records.append(record)
            
            # 按时间排序
            records.sort(key=lambda x: x["recorded_at"])
            return records
        except Exception as e:
            print(f"获取用户用药记录失败: {e}")
            return []
    
    def generate_adherence_report(self, user_id, days=30):
        """
        生成依从性报告
        Args:
            user_id: 用户ID
            days: 统计天数
        Returns:
            报告字典
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            records = self.get_user_records(user_id, start_date, end_date)
            
            # 统计数据
            total_records = len(records)
            taken_records = len([r for r in records if r["status"] == "taken"])
            missed_records = len([r for r in records if r["status"] == "missed"])
            skipped_records = len([r for r in records if r["status"] == "skipped"])
            
            # 计算依从率
            adherence_rate = (taken_records / total_records * 100) if total_records > 0 else 0
            
            # 构建报告
            report = {
                "user_id": user_id,
                "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                "total_days": days,
                "total_records": total_records,
                "taken_records": taken_records,
                "missed_records": missed_records,
                "skipped_records": skipped_records,
                "adherence_rate": round(adherence_rate, 2),
                "generated_at": datetime.now().isoformat()
            }
            
            return report
        except Exception as e:
            print(f"生成依从性报告失败: {e}")
            return None
    
    def get_today_reminders(self, user_id):
        """
        获取今日提醒
        Args:
            user_id: 用户ID
        Returns:
            今日提醒列表
        """
        try:
            today = datetime.now().date()
            reminders = self.get_user_reminders(user_id)
            
            today_reminders = []
            for reminder in reminders:
                if reminder["status"] != "active":
                    continue
                
                start_date = datetime.fromisoformat(reminder["start_date"]).date()
                end_date = datetime.fromisoformat(reminder["end_date"]).date() if reminder["end_date"] else None
                
                if start_date <= today and (not end_date or end_date >= today):
                    today_reminders.append(reminder)
            
            return today_reminders
        except Exception as e:
            print(f"获取今日提醒失败: {e}")
            return []