"""Real-ESRGAN超分辨率模型封装，用于小文本增强

@author: wsy
@date: 2026.01.07
@desc: 提供Real-ESRGAN模型的懒加载实现，优化小文本识别
"""

import os
import requests
import torch

from config import REAL_ESRGAN_WEIGHT, REAL_ESRGAN_URL

# =========================================================
# Torchvision兼容性修复
# 解决: No module named torchvision.transforms.functional_tensor
# =========================================================
import sys
import types

try:
    import torchvision.transforms.functional as F
except ModuleNotFoundError:
    raise ImportError("无法找到 torchvision.transforms.functional 模块，请检查 torchvision 是否已正确安装")

# 创建一个模拟的 functional_tensor 模块
module = types.ModuleType("torchvision.transforms.functional_tensor")

# 映射常用函数到这个模拟的模块中
module.rgb_to_grayscale = F.rgb_to_grayscale
# 替换 _get_image_size 为 get_image_size
module.get_image_size = F.get_image_size
module.to_tensor = F.to_tensor

# 将模拟的模块添加到 sys.modules 中
sys.modules["torchvision.transforms.functional_tensor"] = module



def _ensure_weight():
    """
    确保 Real-ESRGAN 权重存在，不存在则自动下载
    """
    if os.path.exists(REAL_ESRGAN_WEIGHT):
        return REAL_ESRGAN_WEIGHT

    if REAL_ESRGAN_URL is None:
        raise RuntimeError("REAL_ESRGAN_URL 未配置，且本地不存在权重")

    print(f"[Real-ESRGAN] downloading → {REAL_ESRGAN_WEIGHT}")
    r = requests.get(REAL_ESRGAN_URL, timeout=60)
    r.raise_for_status()

    os.makedirs(os.path.dirname(REAL_ESRGAN_WEIGHT), exist_ok=True)
    with open(REAL_ESRGAN_WEIGHT, "wb") as f:
        f.write(r.content)

    return REAL_ESRGAN_WEIGHT


class RealESRGANWrapper:
    def __init__(self, device="cuda", scale=2, model_path=None):
        self.device = device
        self.scale = scale
        self.model_path = model_path
        self._loaded = False
        self.upsampler = None

    def _lazy_load(self):
        if self._loaded:
            return

        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"[Real-ESRGAN] weight not found: {self.model_path}"
            )
        from realesrgan import RealESRGANer, RRDBNet
        
        model = RRDBNet(
            in_nc=3,
            out_nc=3,
            nf=64,
            nb=23,
            scale=self.scale
        )

        self.upsampler = RealESRGANer(
            scale=self.scale,
            model_path=self.model_path,
            model=model,
            tile=256,
            tile_pad=10,
            pre_pad=0,
            half=(self.device == "cuda"),
            device=self.device
        )

        self._loaded = True

    def enhance(self, img):
        self._lazy_load()
        out, _ = self.upsampler.enhance(img, outscale=self.scale)
        return out
