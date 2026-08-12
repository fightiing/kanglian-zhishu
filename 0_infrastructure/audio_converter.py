#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
基础设施层 - 音频转换工具
================================================================================
职责：提供音频格式转换功能，将浏览器录音转换为API可识别的格式
功能：
  - 处理浏览器录音（base64格式）
  - 转换为WAV格式（16kHz采样率，单声道）
  - 调用百度ASR API进行语音识别
  - 将API返回结果保存为JSON格式
================================================================================
"""

import base64
import json
import os
import wave
import numpy as np
from datetime import datetime
from .asr_service import BaiduASR, recognize_b64_audio
from .config import BAIDU_ASR_CONFIG


def convert_base64_to_wav(base64_audio, output_path):
    """
    将base64音频数据转换为WAV格式文件
    
    Args:
        base64_audio: Base64编码的音频数据
        output_path: 输出WAV文件路径
    
    Returns:
        bool: 转换是否成功
    """
    try:
        # 去掉base64前缀（如 data:audio/wav;base64,）
        if ',' in base64_audio:
            base64_audio = base64_audio.split(',')[1]
        
        # 将base64解码为二进制数据
        audio_bytes = base64.b64decode(base64_audio)
        
        # 直接写入WAV文件
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
        
        return True
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False


def process_browser_audio(base64_audio, output_dir="./output"):
    """
    处理浏览器录音并保存API结果到JSON
    
    Args:
        base64_audio: Base64编码的音频数据
        output_dir: 输出目录
    
    Returns:
        dict: 包含转写结果和保存路径的字典
    """
    try:
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存原始音频文件
        audio_filename = os.path.join(output_dir, f"audio_{timestamp}.wav")
        if convert_base64_to_wav(base64_audio, audio_filename):
            print(f"音频已保存到: {audio_filename}")
        else:
            print("音频转换失败，跳过保存")
        
        # 调用ASR服务进行识别，并自动保存JSON结果
        transcript = recognize_b64_audio(base64_audio, save_to_json=True, output_dir=output_dir)
        
        # 返回结果
        result = {
            "transcript": transcript,
            "audio_saved": audio_filename if os.path.exists(audio_filename) else None,
            "json_saved": os.path.join(output_dir, f"asr_result_{timestamp}.json")
        }
        
        print(f"语音识别结果: {transcript}")
        print(f"API结果已保存到JSON文件")
        
        return result
        
    except Exception as e:
        print(f"处理音频失败: {str(e)}")
        return None


def create_recording_client():
    """
    创建一个录音客户端，用于演示如何从浏览器获取录音并处理
    """
    asr = BaiduASR(
        app_id=BAIDU_ASR_CONFIG['APP_ID'],
        api_key=BAIDU_ASR_CONFIG['API_KEY'],
        secret_key=BAIDU_ASR_CONFIG['SECRET_KEY']
    )
    return asr


def example_usage():
    """
    使用示例
    """
    print("=== 音频转换工具使用示例 ===")
    
    # 示例：模拟浏览器录音数据（实际使用时会从前端接收）
    # 这里我们使用一个示例base64字符串，实际使用时会从前端获取
    sample_base64_audio = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQQAAAAAAAAAAAA="
    
    # 处理音频
    result = process_browser_audio(sample_base64_audio, "./output")
    
    if result:
        print(f"转写结果: {result['transcript']}")
        print(f"音频文件: {result['audio_saved']}")
        print(f"JSON结果: {result['json_saved']}")


if __name__ == "__main__":
    example_usage()