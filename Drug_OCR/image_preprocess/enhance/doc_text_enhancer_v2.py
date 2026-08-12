"""药品说明书文本图像增强器，优化OCR识别精度

@author: wsy
@date: 2026.01.07
@desc: 基于多尺度背景估计和DoG算法的文本增强模块
"""

import cv2
import numpy as np


class DocTextEnhancerV2:
    """药品说明书专用文本增强器
    
    算法特性:
    - 多尺度背景估计保护细小文字
    - DoG(高斯差分)增强字形轮廓
    - 低强度CLAHE防止过增强
    - 非均匀光照和阴影消除
    
    设计原则:
    - OCR准确率优先于视觉效果
    - 保持医学文本的严谨性
    """

    def enhance(self, img):
        if img is None or img.size == 0:
            return img

        # 1. 灰度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ===============================
        # 2. 多尺度背景估计（关键提升点）
        # ===============================
        bg_large = cv2.morphologyEx(
            gray,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (45, 45))
        )

        bg_small = cv2.morphologyEx(
            gray,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        )

        # 融合背景（避免吃掉小字）
        bg = cv2.addWeighted(bg_large, 0.7, bg_small, 0.3, 0)

        # 3. 去背景 + 归一化
        norm = cv2.subtract(gray, bg)
        norm = cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX)

        # ===============================
        # 4. 低强度 CLAHE（防止噪声爆炸）
        # ===============================
        clahe = cv2.createCLAHE(
            clipLimit=1.8,
            tileGridSize=(8, 8)
        )
        contrast = clahe.apply(norm)

        # ===============================
        # 5. DoG（Difference of Gaussian）增强字形
        # 比锐化安全得多
        # ===============================
        blur1 = cv2.GaussianBlur(contrast, (0, 0), 0.6)
        blur2 = cv2.GaussianBlur(contrast, (0, 0), 1.4)
        dog = cv2.subtract(blur1, blur2)

        enhanced = cv2.addWeighted(
            contrast, 1.0,
            dog, 1.2,
            0
        )

        # ===============================
        # 6. 轻度去噪（只压背景，不吃字）
        # ===============================
        final = cv2.fastNlMeansDenoising(
            enhanced,
            None,
            h=7,
            templateWindowSize=7,
            searchWindowSize=21
        )

        return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
