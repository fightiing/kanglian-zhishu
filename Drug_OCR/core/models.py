"""
核心数据模型定义模块

@author: wsy
@date: 2026.01.07
@desc: 定义药品说明书识别引擎使用的数据模型
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EngineResult:
    """药品说明书识别结果数据模型
    
    Attributes:
        drug_name (Optional[str]): 药品名称，可能为空
        structured_text (Dict[str, str]): 结构化识别结果
        full_text (str): 完整识别文本
        raw_ocr_text (str): 原始OCR识别文本
        llm_used (bool): 是否使用了LLM处理
    """
    drug_name: Optional[str]
    structured_text: Dict[str, str]
    full_text: str
    raw_ocr_text: str
    llm_used: bool
