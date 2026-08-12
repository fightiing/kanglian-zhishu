"""基于Retinex理论的低光图像增强器（补丁式实现）

@author: wsy
@date: 2026.01.07
@desc: 采用分块处理策略实现大尺寸图像的低光增强
"""

import cv2
import torch
import numpy as np

from .models.retinex_net import RetinexNet


class RetinexPatchEnhancer:
    """Retinex低光增强器（补丁式实现）
    
    功能特性:
    - 基于Retinex理论的深度学习实现
    - 支持大尺寸图像的分块处理
    - 自动处理边界重叠区域
    
    参数说明:
    - patch_size: 处理块大小(默认256)
    - overlap: 块重叠区域(默认32)
    """

    def __init__(
        self,
        model_path,
        device="cuda",
        patch_size=256,
        overlap=32
    ):
        """初始化增强器
        
        Args:
            model_path: 预训练模型路径
            device: 计算设备(cpu/cuda)
            patch_size: 处理块大小
            overlap: 块重叠区域
        """
        self.device = device
        self.patch_size = patch_size
        self.overlap = overlap

        self.model = RetinexNet().to(device)
        ckpt = torch.load(model_path, map_location=device)
        self.model.load_state_dict(ckpt["model"])
        self.model.eval()

    @torch.no_grad()
    def enhance(self, img_bgr: np.ndarray) -> np.ndarray:
        if img_bgr is None:
            raise ValueError("img_bgr is None")

        if img_bgr.ndim != 3:
            raise ValueError(f"img_bgr ndim != 3, got {img_bgr.shape}")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = img_rgb.shape
        stride = self.patch_size - self.overlap

        output = np.zeros((h, w, 3), dtype=np.float32)
        weight = np.zeros((h, w, 3), dtype=np.float32)

        for y in range(0, h, stride):
            for x in range(0, w, stride):
                y1 = min(y + self.patch_size, h)
                x1 = min(x + self.patch_size, w)
                y0 = max(0, y1 - self.patch_size)
                x0 = max(0, x1 - self.patch_size)

                patch = img_rgb[y0:y1, x0:x1]
                ph, pw = patch.shape[:2]

                if ph < self.patch_size or pw < self.patch_size:
                    pad = np.zeros(
                        (self.patch_size, self.patch_size, 3),
                        dtype=np.uint8
                    )
                    pad[:ph, :pw] = patch
                    patch = pad

                x_tensor = (
                    torch.from_numpy(patch.astype(np.float32) / 255.0)
                    .permute(2, 0, 1)
                    .unsqueeze(0)
                    .to(self.device)
                )

                # ===== 关键修复点：通用解包 =====
                out = self.model(x_tensor)

                # 如果 forward 返回 tuple/list（训练常见）
                if isinstance(out, (tuple, list)):
                    out = out[0]

                # 如果还有 batch 维
                if out.dim() == 4:
                    out = out.squeeze(0)

                if out.dim() != 3:
                    raise RuntimeError(
                        f"Unexpected model output shape: {out.shape}"
                    )

                out = (
                    out.clamp(0, 1)
                    .permute(1, 2, 0)
                    .cpu()
                    .numpy()
                )

                out = out[:ph, :pw]
                output[y0:y1, x0:x1] += out
                weight[y0:y1, x0:x1] += 1.0

        output = output / np.maximum(weight, 1e-6)
        output = (output * 255.0).round().astype(np.uint8)
        return cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
