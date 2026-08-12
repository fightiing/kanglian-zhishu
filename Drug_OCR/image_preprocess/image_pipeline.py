"""OCR图像预处理流水线，优化药品说明书图像质量

@author: wsy
@date: 2026.01.07
@desc: 提供端到端的图像预处理流程，提升OCR识别准确率
"""

import cv2
import numpy as np

from config import RETINEX_WEIGHT, DocLayout_YOLO
from image_preprocess.enhance.retinex_patch import RetinexPatchEnhancer
from image_preprocess.super_res.real_esrgan import RealESRGANWrapper
from image_preprocess.enhance.doc_text_enhancer_v2 import DocTextEnhancerV2
from layout.yolo_layout_detector import YoloLayoutDetector
from layout.block_builder import build_blocks


class ImagePreprocessPipeline:
    """药品说明书图像预处理流水线
    
    功能特性:
    - 多阶段图像增强流程
    - 自适应条件处理(低光/小文字等)
    - 基于区域的精细化处理
    
    处理流程:
    1. 低光增强(条件触发)
    2. 全局文本增强
    3. 版面分析与区域提取
    4. 区域级精细化处理
    """

    def __init__(self, device="cuda"):
        self.device = device

        # ========= 核心增强器（始终使用） =========
        self.text_enhancer = DocTextEnhancerV2()

        # ========= 条件模型（lazy-load） =========
        self.lowlight = RetinexPatchEnhancer(
            model_path=RETINEX_WEIGHT,
            device=device
        )

        self.superres = RealESRGANWrapper(
            device=device,
            scale=2   # ⚠️ OCR 友好，禁止 x4
        )

        # ========= 版面检测 =========
        self.yolo = YoloLayoutDetector()

    # -------------------------------------------------
    # 条件判断
    # -------------------------------------------------
    def _is_low_light(self, img_bgr, thresh=60):
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        return gray.mean() < thresh

    def _need_superres(self, roi):
        h, w = roi.shape[:2]
        return min(h, w) < 900

    # -------------------------------------------------
    # 主处理流程
    # -------------------------------------------------
    def process(self, img_bgr):
        """
        输入：BGR uint8
        输出：BGR uint8（OCR 友好）
        """
        assert img_bgr is not None and img_bgr.size > 0

        h0, w0 = img_bgr.shape[:2]
        out = img_bgr

        # ===== 1. 低光才启用 Retinex =====
        if self._is_low_light(out):
            out = self.lowlight.enhance(out)

        # ===== 2. 核心 OCR 友好增强 =====
        out = self.text_enhancer.enhance(out)

        # ===== 3. YOLO 文本区域检测 =====
        yolo_results = self.yolo.detect(out)
        blocks = build_blocks(yolo_results)

        if not blocks:
            return self._resize_back(out, w0, h0)

        # ===== 4. ROI 级增强（轻） =====
        final_img = out.copy()

        for block in blocks:
            if block.get("type") not in ("title", "header", "text"):
                continue

            x1, y1, x2, y2 = map(int, block["bbox"])
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w0, x2), min(h0, y2)

            roi = final_img[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # 二次 DocTextEnhancer（ROI 更稳）
            roi = self.text_enhancer.enhance(roi)

            # 小字才用 ESRGAN
            if self._need_superres(roi) and (x2 - x1) > 120:
                try:
                    roi = self.superres.enhance(roi)
                    roi = cv2.resize(roi, (x2 - x1, y2 - y1))
                except Exception:
                    pass

            final_img[y1:y2, x1:x2] = roi

        return self._resize_back(final_img, w0, h0)

    # -------------------------------------------------
    # 工具
    # -------------------------------------------------
    def _resize_back(self, img, w, h):
        if img.shape[1] != w or img.shape[0] != h:
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
        return img
