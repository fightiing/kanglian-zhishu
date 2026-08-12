# from typing import Any, Dict
# 运行时间短，没有使用YOLO版面检测，所以注释掉了
# from ocr.ocr_engine import RapidOCREngine
# from ai.llm_structured_extractor import LLMStructuredExtractor
# from core.models import EngineResult


# class RecognitionPipeline:
#     """
#     图像 → OCR → LLM → 规整说明书
#     """

#     def __init__(self):
#         self.ocr_engine = RapidOCREngine()
#         self.llm_extractor = LLMStructuredExtractor()

#     def run(self, image_path: str) -> EngineResult:
#         # 1️⃣ OCR（只负责“把字读出来”）
#         ocr_lines = self.ocr_engine.recognize(image_path)
#         raw_text = "\n".join(
#             l["text"] for l in ocr_lines if l.get("text")
#         )

#         # 2️⃣ LLM：一次性结构化说明书
#         structured = self.llm_extractor.extract(raw_text)

#         # 3️⃣ 生成最终规整文本
#         full_text = self._build_full_text(structured)

#         return EngineResult(
#             drug_name=structured.get("药品名称"),
#             structured_text=structured,
#             full_text=full_text,
#             raw_ocr_text=raw_text,
#             llm_used=True,
#         )

#     def _build_full_text(self, structured: Dict[str, Any]) -> str:
#         parts = []

#         for key, value in structured.items():
#             if not value:
#                 continue

#             # ✅ 普通字符串字段
#             if isinstance(value, str):
#                 text = value.strip()
#                 if text:
#                     parts.append(f"【{key}】\n{text}")

#             # ✅ 子结构（如：特殊人群用药）
#             elif isinstance(value, dict):
#                 sub_parts = []
#                 for sub_key, sub_val in value.items():
#                     if sub_val and isinstance(sub_val, str):
#                         sub_parts.append(f"{sub_key}：{sub_val.strip()}")

#                 if sub_parts:
#                     parts.append(f"【{key}】\n" + "\n".join(sub_parts))

#         return "\n\n".join(parts)

from typing import Any, Dict, List
from pathlib import Path

# 把重型依赖改为延迟导入，避免云端安装失败时整个服务崩溃
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    HAS_CV2 = False

try:
    from ocr.ocr_engine import RapidOCREngine
    HAS_RAPIDOCR = True
except ImportError:
    RapidOCREngine = None
    HAS_RAPIDOCR = False

try:
    from ai.llm_structured_extractor import LLMStructuredExtractor
    HAS_LLM_EXTRACTOR = True
except ImportError:
    LLMStructuredExtractor = None
    HAS_LLM_EXTRACTOR = False

from core.models import EngineResult

try:
    from layout.yolo_layout_detector import YoloLayoutDetector
    from layout.block_builder import build_blocks
    from layout.block_sorter import sort_blocks_reading_order
    HAS_LAYOUT = True
except ImportError:
    YoloLayoutDetector = None
    build_blocks = None
    sort_blocks_reading_order = None
    HAS_LAYOUT = False


class RecognitionPipeline:
    """
    图像 → 图像增强 → YOLO版面检测 → 块级OCR → LLM → 规整说明书
    """

    def __init__(self, device: str = "cpu"):
        if not HAS_CV2:
            raise ImportError("opencv-python 未安装，OCR管线不可用")
        if not HAS_RAPIDOCR:
            raise ImportError("rapidocr-onnxruntime 未安装，OCR管线不可用")
        if not HAS_LLM_EXTRACTOR:
            raise ImportError("LLM提取器依赖未安装，OCR管线不可用")
        if not HAS_LAYOUT:
            raise ImportError("版面检测依赖未安装，OCR管线不可用")
        self.ocr_engine = RapidOCREngine()
        self.llm_extractor = LLMStructuredExtractor()
        self.yolo_detector = YoloLayoutDetector(device=device)

    def run(self, image_path: str) -> EngineResult:
        # =========================
        # 1️⃣ 读取图像
        # =========================
        image_path = str(image_path)
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("无法读取图像文件")

        img_h, img_w = img.shape[:2]

        # =========================
        # 2️⃣ YOLO 版面检测
        # =========================
        layout_results = self.yolo_detector.detect(img)

        # =========================
        # 3️⃣ 构建并排序版面块
        # =========================
        blocks = build_blocks(layout_results)
        blocks = sort_blocks_reading_order(
            blocks,
            img_w=img_w,
            img_h=img_h
        )

        # =========================
        # 4️⃣ 基于版面块进行 OCR
        # =========================
        ocr_blocks = self._ocr_by_blocks(img, blocks)

        # =========================
        # 5️⃣ 拼接为“阅读顺序文本”
        # =========================
        raw_text = self._assemble_text(ocr_blocks)

        # =========================
        # 6️⃣ LLM 结构化解析
        # =========================
        structured = self.llm_extractor.extract(raw_text)

        # =========================
        # 7️⃣ 生成规整说明书
        # =========================
        full_text = self._build_full_text(structured)

        return EngineResult(
            drug_name=structured.get("药品名称"),
            structured_text=structured,
            full_text=full_text,
            raw_ocr_text=raw_text,
            llm_used=True,
        )

    # =====================================================
    # 内部工具函数
    # =====================================================

    def _ocr_by_blocks(self, img, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对每个版面块进行 OCR
        """
        results = []

        for block in blocks:
            x1, y1, x2, y2 = map(int, block["bbox"])

            # 防御性裁剪
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                continue

            crop = img[y1:y2, x1:x2]

            lines = self.ocr_engine.recognize(crop)
            text = "\n".join(
                l["text"] for l in lines if l.get("text")
            ).strip()

            if not text:
                continue

            results.append({
                "type": block.get("type", "text"),
                "bbox": block["bbox"],
                "text": text
            })

        return results

    def _assemble_text(self, ocr_blocks: List[Dict[str, Any]]) -> str:
        """
        按阅读顺序拼接 OCR 文本
        """
        parts = []
        for b in ocr_blocks:
            t = b["text"].strip()
            if t:
                parts.append(t)
        return "\n\n".join(parts)

    def _build_full_text(self, structured: Dict[str, Any]) -> str:
        """
        将结构化说明书转换为可阅读文本
        """
        parts = []

        for key, value in structured.items():
            if not value:
                continue

            if isinstance(value, str):
                text = value.strip()
                if text:
                    parts.append(f"【{key}】\n{text}")

            elif isinstance(value, dict):
                sub_parts = []
                for sub_key, sub_val in value.items():
                    if sub_val and isinstance(sub_val, str):
                        sub_parts.append(f"{sub_key}：{sub_val.strip()}")

                if sub_parts:
                    parts.append(f"【{key}】\n" + "\n".join(sub_parts))

        return "\n\n".join(parts)
