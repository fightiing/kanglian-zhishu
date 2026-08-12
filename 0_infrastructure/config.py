#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
基础设施层 - 配置管理
================================================================================
职责：统一管理所有第三方服务的API密钥和配置参数
包含：百度AI（TTS/ASR/OCR）、Neo4j、Ollama等
================================================================================
"""

# ==================== 百度AI开放平台配置 ====================
# 百度语音识别(ASR)配置
BAIDU_ASR_CONFIG = {
    'APP_ID': '121737904',  # 从example.py获取
    'API_KEY': 'XoS1fCGzqKiz45sXvoLIgLL9',  # 从example.py获取
    'SECRET_KEY': 'weErgxvvk76vVF5wBFAEtIXERnons2An'  # 从example.py获取
}

# 百度语音合成(TTS)配置
BAIDU_TTS_CONFIG = {
    'APP_ID': '121763026',
    'API_KEY': 'oPhr0bjeh6Tas0Yl9pHAQF8J',
    'SECRET_KEY': 'xGkgcZU9q0exXtTB5mazejM8Z6HxJQ5A'
}

# 百度OCR配置（文字识别）
BAIDU_OCR_CONFIG = {
    'APP_ID': '116644568',
    'API_KEY': 'GS98RqI6FNbvQGq7OzElrTbG',
    'SECRET_KEY': 'RbNWTGM4eXHV3SYZ0m3lTI4OGeGdPT4B'
}


# ==================== Neo4j知识图谱配置 ====================   这里需要使用正确的neo4j数据配置
NEO4J_CONFIG = {
    'URI': 'neo4j://localhost:7687',
    'USERNAME': 'neo4j',
    'PASSWORD': '12345678'
}


# ==================== Ollama大模型配置 ====================
OLLAMA_CONFIG = {
    'BASE_URL': 'http://localhost:11434',
    'MODEL': 'deepseek-r1:8b',
    'TEMPERATURE': 0.3,
    'MAX_TOKENS': 1024
}


# ==================== 应用配置 ====================
APP_CONFIG = {
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'DEBUG': True
}
