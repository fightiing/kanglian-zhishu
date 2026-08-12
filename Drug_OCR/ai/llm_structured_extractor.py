import json
import re
from typing import Dict, Any

from ai.llm_client import LLMClient


class LLMStructuredExtractor:
    """
    OCR 文本 → 结构化说明书（LLM）
    - 强 JSON 提取
    - 永不信任 LLM 输出
    - 工程级兜底
    """

    def __init__(self):
        self.client = LLMClient()

    def extract(self, ocr_text: str) -> Dict[str, Any]:
        if not ocr_text or len(ocr_text.strip()) < 20:
            raise RuntimeError("OCR 文本为空或过短")

        prompt = self._build_prompt(ocr_text)
        resp = self.client.generate(prompt)

        data = self._safe_parse_json(resp)
        if data is None:
            # 打印部分原始输出，方便你调试
            preview = resp[:500] if resp else "EMPTY"
            raise RuntimeError(f"LLM 未返回合法 JSON，原始输出片段:\n{preview}")

        return data

    # =====================================================
    # 🔒 JSON 安全解析（核心修复点）
    # =====================================================
    def _safe_parse_json(self, text: str) -> Dict[str, Any] | None:
        if not text:
            return None

        # 1️⃣ 去除 Markdown 包裹
        cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

        # 2️⃣ 直接尝试解析
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 3️⃣ 尝试提取第一个 JSON 对象
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return None

        return None

    def _build_prompt(self, text: str) -> str:
        return PROMPT_TEMPLATE.replace("{{OCR_TEXT}}", text)


# =====================================================
# Prompt（不改语义，只增强约束）
# =====================================================
PROMPT_TEMPLATE = """你是一名【中文药品说明书结构化抽取助手】。

下面是一段 OCR 识别得到的药品说明书原文，存在错别字、换行混乱、符号错误。

你的任务：
1. 纠正明显 OCR 错误（如：口暇→口服）
2. 按【国家药监局说明书规范】整理结构
3. 不添加原文中不存在的医学信息
4. 不进行医学推断
5. 仅输出 JSON，不要任何解释、不要 Markdown

⚠️ 必须严格只输出 JSON，对象结构如下（字段必须齐全，缺失填空字符串 ""）：

{
  "药品名称": "",
  "成分": "",
  "功能主治": "",
  "适应症": "",
  "用法用量": "",
  "不良反应": "",
  "禁忌": "",
  "注意事项": "",
  "药物相互作用": "",
  "特殊人群用药": {
    "孕妇": "",
    "哺乳期妇女": "",
    "儿童": "",
    "老年人": "",
    "肝肾功能不全": ""
  },
  "贮藏": "",
  "包装": "",
  "有效期": "",
  "执行标准": "",
  "批准文号": "",
  "上市许可持有人": "",
  "生产企业": ""
}

【OCR 原文】
<<<
{{OCR_TEXT}}
>>>
"""
