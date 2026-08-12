#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
基础设施层 (Infrastructure Layer)
================================================================================
职责：提供全局通用技术服务，零业务依赖
包含：
  - tts_service: 语音合成(TTS)，全局语音播报
  - asr_service: 语音识别(ASR)，语音转文字
  - ocr_service: 图像识别(OCR)，文字识别（待实现）
  - config: 统一配置管理

特性：
  ✅ 全局单例模式，避免重复初始化
  ✅ 零业务依赖，纯技术能力封装
  ✅ 统一调用接口，简化使用

使用示例：
    from infrastructure.tts_service import speak
    from infrastructure.asr_service import recognize
    
    # 语音播报
    speak("布洛芬缓释胶囊")
    
    # 语音识别
    text = recognize(audio_bytes)
================================================================================
"""

from .tts_service import speak, get_tts_instance
from .asr_service import recognize, get_asr_instance
from .config import (
    BAIDU_TTS_CONFIG,
    BAIDU_ASR_CONFIG,
    BAIDU_OCR_CONFIG,
    NEO4J_CONFIG,
    OLLAMA_CONFIG,
    APP_CONFIG
)

__all__ = [
    # TTS服务
    'speak',
    'get_tts_instance',
    
    # ASR服务
    'recognize',
    'get_asr_instance',
    
    # 配置
    'BAIDU_TTS_CONFIG',
    'BAIDU_ASR_CONFIG',
    'BAIDU_OCR_CONFIG',
    'NEO4J_CONFIG',
    'OLLAMA_CONFIG',
    'APP_CONFIG',
]
