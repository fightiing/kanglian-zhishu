"""基于YOLOv10的药品说明书版面检测器

@author: wsy
@date: 2026.01.07
@desc: 使用DocLayout-YOLO模型检测药品说明书中的文本区域和结构
"""

from pathlib import Path
import cv2
import os
from huggingface_hub import hf_hub_download

# 设置Ultralytics配置目录到D盘，避免权限问题
os.environ['ULTRALYTICS_HOME'] = 'D:/ai_models/ultralytics'

from doclayout_yolo import YOLOv10
from config import DocLayout_YOLO, MODEL_HOME

class YoloLayoutDetector:
    """药品说明书版面检测器(YOLOv10实现)
    
    功能特性:
    - 自动下载预训练模型
    - 支持多种版面元素检测(标题、正文等)
    - 返回带置信度的检测结果
    
    参数说明:
    - device: 计算设备(cpu/cuda)
    - model_path: 自定义模型路径(可选)
    """

    def __init__(self, device="cpu"):
        
        model_path = Path(DocLayout_YOLO)
        print(f"DocLayout-YOLO model path: {model_path}")

        if not model_path.exists() or model_path.suffix.lower() != ".pt":
            model_path = Path(
                hf_hub_download(
                    repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
                    filename="doclayout_yolo_docstructbench_imgsz1024.pt",
                    local_dir=str(Path(MODEL_HOME).expanduser())
                )
            )

        self.model = YOLOv10(str(model_path))
        self.device = device

        self.class_names = self.model.names

    def detect(self, image_bgr):
        
        results = self.model.predict(
            source=image_bgr,
            device=self.device,
            imgsz=1024,   
            conf=0.25,
            iou=0.5,
            verbose=False
        )

        blocks = []
        r = results[0]
        if r.boxes is None:
            return blocks

        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = self.class_names[cls_id]
            score = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            blocks.append({"label": label, "score": score, "bbox": [x1, y1, x2, y2]})

        return blocks