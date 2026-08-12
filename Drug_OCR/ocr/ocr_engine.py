# """药品说明书OCR引擎实现(RapidOCR封装)

# @author: wsy
# @date: 2026.01.07
# @desc: 基于RapidOCR的高精度药品说明书文字识别
# """

# from rapidocr_onnxruntime import RapidOCR


# class RapidOCREngine:
#     """药品说明书OCR识别引擎
    
#     功能特性:
#     - 基于PP-OCRv4中英文识别模型
#     - 返回行级结构化识别结果
#     - 支持置信度过滤
    
#     模型配置:
#     - 检测模型: ch_PP-OCRv4_det
#     - 识别模型: ch_PP-OCRv4_rec
#     - 启用方向分类器
#     """

#     def __init__(self):
#         """初始化OCR引擎
        
#         使用默认的PP-OCRv4模型配置
#         """
#         self.ocr = RapidOCR(
#             det_model_name="ch_PP-OCRv4_det",
#             rec_model_name="ch_PP-OCRv4_rec",
#             use_angle_cls=True
#         )

#     def recognize(self, img, score_thresh=0.5):
#         """
#         返回：行级 OCR 结果
#         [
#           {
#             text, score,
#             x1,y1,x2,y2,
#             cx, cy
#           }
#         ]
#         """
#         result, _ = self.ocr(img)
#         if not result:
#             return []

#         lines = []
#         for quad, text, score in result:
#             score = float(score)
#             if score < score_thresh or not text.strip():
#                 continue

#             xs = [p[0] for p in quad]
#             ys = [p[1] for p in quad]
#             x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)

#             lines.append({
#                 "text": text.strip(),
#                 "score": score,
#                 "x1": x1, "y1": y1, "x2": x2, "y2": y2,
#                 "cx": (x1 + x2) / 2,
#                 "cy": (y1 + y2) / 2,
#             })

#         return lines
"""药品说明书OCR引擎实现(RapidOCR封装)

@author: wsy
@date: 2026.01.07
@desc: 基于RapidOCR的高精度药品说明书文字识别
"""

from rapidocr_onnxruntime import RapidOCR
import os
from pathlib import Path

class RapidOCREngine:
    """药品说明书OCR识别引擎
    
    功能特性:
    - 基于PP-OCRv4中英文识别模型
    - 返回行级结构化识别结果
    - 支持置信度过滤
    
    模型配置:
    - 检测模型: ch_PP-OCRv4_det
    - 识别模型: ch_PP-OCRv4_rec
    - 启用方向分类器
    """

    def __init__(self):
        """初始化OCR引擎
        
        使用默认的PP-OCRv4模型配置
        """
        # 尝试多种方式初始化RapidOCR
        self.ocr = self._init_rapidocr()

    def _init_rapidocr(self):
        """初始化RapidOCR，处理模型路径问题"""
        try:
            # 方式1：直接使用模型名称（可能会自动下载，但可能失败）
            return RapidOCR(
                det_model_name="ch_PP-OCRv4_det",
                rec_model_name="ch_PP-OCRv4_rec",
                use_angle_cls=True
            )
        except Exception as e:
            print(f"方式1失败: {e}")
            
            try:
                # 方式2：指定模型路径
                model_dir = Path("D:/ai_models/rapidocr")
                
                # 检查模型文件是否存在
                det_path = model_dir / "ch_PP-OCRv4_det_infer.onnx"
                rec_path = model_dir / "ch_PP-OCRv4_rec_infer.onnx"
                cls_path = model_dir / "ch_ppocr_mobile_v2.0_cls_infer.onnx"
                
                if not det_path.exists():
                    raise FileNotFoundError(f"检测模型不存在: {det_path}")
                if not rec_path.exists():
                    raise FileNotFoundError(f"识别模型不存在: {rec_path}")
                
                print(f"使用本地模型: {det_path}")
                
                return RapidOCR(
                    det_model_path=str(det_path),
                    rec_model_path=str(rec_path),
                    cls_model_path=str(cls_path) if cls_path.exists() else None,
                    use_angle_cls=cls_path.exists()
                )
                
            except Exception as e2:
                print(f"方式2也失败: {e2}")
                
                # 方式3：使用在线模型，设置超时和重试
                print("尝试从网络下载模型...")
                try:
                    return RapidOCR(
                        det_model_name="ch_PP-OCRv4_det",
                        rec_model_name="ch_PP-OCRv4_rec",
                        use_angle_cls=True,
                        download_model=True  # 强制下载模型
                    )
                except Exception as e3:
                    print(f"所有方式都失败: {e3}")
                    raise RuntimeError("无法初始化RapidOCR引擎")

    def recognize(self, img, score_thresh=0.5):
        """
        返回：行级 OCR 结果
        [
          {
            text, score,
            x1,y1,x2,y2,
            cx, cy
          }
        ]
        """
        if not hasattr(self, 'ocr') or self.ocr is None:
            print("OCR引擎未初始化")
            return []

        try:
            result, _ = self.ocr(img)
            if not result:
                return []

            lines = []
            for quad, text, score in result:
                score = float(score)
                if score < score_thresh or not text.strip():
                    continue

                xs = [p[0] for p in quad]
                ys = [p[1] for p in quad]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)

                lines.append({
                    "text": text.strip(),
                    "score": score,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "cx": (x1 + x2) / 2,
                    "cy": (y1 + y2) / 2,
                })

            return lines
            
        except Exception as e:
            print(f"OCR识别过程出错: {e}")
            return []