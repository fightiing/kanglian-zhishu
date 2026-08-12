#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
基础设施层 - 语音合成服务(TTS)
================================================================================
职责：提供全局语音播报能力，被所有业务模块调用
特性：
  - 全局单例模式，避免重复初始化
  - 老年友好参数预设（语速4、音量7、女声）
  - 文本自动简化，剔除专业术语
  - 零业务依赖，纯技术服务
  - 本地备选方案，当百度API不可用时使用

技术栈：百度AI语音合成 + 本地备选方案
调用方式：
    from infrastructure.tts_service import speak
    speak("布洛芬缓释胶囊，一次1粒，每天2次")
================================================================================
"""

try:
    from aip import AipSpeech
except ImportError:
    AipSpeech = None
    print("WARNING 百度AI SDK未安装，TTS服务将使用本地备选方案")
import base64
import os
import sys
import io

# 动态导入config（解决相对导入问题）
config_path = os.path.join(os.path.dirname(__file__), 'config.py')
if os.path.exists(config_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    BAIDU_TTS_CONFIG = config.BAIDU_TTS_CONFIG
else:
    # 默认配置
    BAIDU_TTS_CONFIG = {
        'APP_ID': '121763026',
        'API_KEY': 'oPHr0bj6ehTas0YI9PHAQF8J',
        'SECRET_KEY': 'xGkgcZUg9oexXTB5mazeIjM8ZH6xJQ5A'
    }


def get_local_tts_audio(text):
    """
    本地文本转语音备选方案
    当百度API不可用时使用
    """
    try:
        # 尝试使用pyttsx3作为本地备选方案
        import pyttsx3
        engine = pyttsx3.init()
        
        # 设置参数
        engine.setProperty('rate', 150)  # 语速
        engine.setProperty('volume', 1.0)  # 音量
        
        # 保存音频到内存
        audio_io = io.BytesIO()
        
        # 使用临时文件保存
        temp_file = 'temp_tts.wav'
        engine.save_to_file(text, temp_file)
        engine.runAndWait()
        
        # 读取文件内容
        if os.path.exists(temp_file):
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            os.remove(temp_file)
            
            # 转换为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return audio_base64
    except Exception as e:
        print(f"本地TTS失败: {e}")
    
    # 如果所有方案都失败，返回空字符串
    return ""


class BaiduTTS:
    """百度语音合成封装类"""
    
    def __init__(self, app_id, api_key, secret_key):
        """
        初始化百度TTS客户端
        Args:
            app_id: 百度应用ID
            api_key: API密钥
            secret_key: 安全密钥
        """
        if AipSpeech is None:
            self.client = None
            print("WARNING AipSpeech不可用，TTS将使用本地备选方案")
        else:
            self.client = AipSpeech(app_id, api_key, secret_key)
        
        # 老年适配默认参数(锁定)
        self.default_params = {
            'spd': 4,   # 语速(0-15), 4为适中偏慢
            'vol': 7,   # 音量(0-15), 7为较大音量
            'per': 0    # 发音人(0女声, 1男声, 3情感男声, 4情感女声)
        }
    
    def synthesize(self, text, spd=None, vol=None, per=None):
        """
        语音合成 - 全局通用接口
        
        Args:
            text: 待播报文字(自动简化处理)
            spd: 语速(可选,默认4)
            vol: 音量(可选,默认7)
            per: 发音人(可选,默认0女声)
        
        Returns:
            Base64编码的MP3音频数据
        """
        # 使用默认参数(如未指定)
        params = {
            'spd': spd if spd is not None else self.default_params['spd'],
            'vol': vol if vol is not None else self.default_params['vol'],
            'per': per if per is not None else self.default_params['per']
        }
        
        # 简化文本(适配老人理解)
        simplified_text = self._simplify_text(text)
        
        # 百度TTS服务的文本长度限制
        MAX_TEXT_LENGTH = 200
        
        # 检查文本长度，如果过长则分割
        if len(simplified_text) > MAX_TEXT_LENGTH:
            # 分割文本
            parts = []
            current_part = ""
            
            # 按句子分割
            sentences = simplified_text.split('。')
            for sentence in sentences:
                if len(current_part) + len(sentence) + 1 <= MAX_TEXT_LENGTH:
                    current_part += sentence + '。'
                else:
                    if current_part:
                        parts.append(current_part)
                    current_part = sentence + '。'
            
            if current_part:
                parts.append(current_part)
            
            # 只取第一部分进行合成（避免合成多个音频）
            simplified_text = parts[0]
        
        try:
            # 调用百度TTS
            result = self.client.synthesis(
                simplified_text,
                'zh',
                1,
                params
            )
            
            # 判断是否成功
            if not isinstance(result, dict):
                # 成功返回音频二进制数据
                audio_base64 = base64.b64encode(result).decode('utf-8')
                return audio_base64
            else:
                # 失败返回错误信息
                print(f"百度TTS合成失败: {result}")
                # 尝试本地备选方案
                return get_local_tts_audio(simplified_text)
        except Exception as e:
            print(f"百度TTS调用失败: {e}")
            # 尝试本地备选方案
            return get_local_tts_audio(simplified_text)

    def _simplify_text(self, text):
        """
        简化播报文字(适配老人理解能力)
        只做术语替换，不限制长度
        """
        # 专业术语替换表
        replacements = {
            '口服': '吃',
            '用法用量': '怎么吃',
            '不良反应': '副作用',
            '禁忌': '不能吃的情况',
            'bid': '每天两次',
            'tid': '每天三次',
            'qd': '每天一次',
            'qn': '睡前',
            'pc': '饭后',
            'ac': '饭前'
        }

        simplified = text
        for old, new in replacements.items():
            simplified = simplified.replace(old, new)

        # 移除长度限制，让TTS服务处理长文本
        return simplified


# ==================== 全局单例模式 ====================
_tts_instance = None


def get_tts_instance():
    """获取全局TTS实例（懒加载）"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = BaiduTTS(
            app_id=BAIDU_TTS_CONFIG['APP_ID'],
            api_key=BAIDU_TTS_CONFIG['API_KEY'],
            secret_key=BAIDU_TTS_CONFIG['SECRET_KEY']
        )
    return _tts_instance


def speak(text, **kwargs):
    """
    【全局TTS调用入口】
    快捷语音播报函数 - 所有业务模块均可调用
    
    使用示例:
        # 药品识别模块
        from infrastructure.tts_service import speak
        speak("布洛芬缓释胶囊，一次1粒，每天2次")
        
        # 语音咨询模块
        speak(answer_text)
        
        # 医生推荐模块
        speak("推荐张医生，心内科，距离1.2公里")
    
    Args:
        text: 待播报文字
        **kwargs: 可选参数(spd, vol, per)
    
    Returns:
        Base64编码的音频数据
    """
    try:
        tts = get_tts_instance()
        return tts.synthesize(text, **kwargs)
    except Exception as e:
        print(f"TTS服务失败: {e}")
        # 直接使用本地备选方案
        return get_local_tts_audio(text)
