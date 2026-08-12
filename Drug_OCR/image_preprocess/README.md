# 图像处理模块文档

## 模块概述
本模块提供图像增强和超分辨率功能，包含：
- RetinexNet图像增强
- Real-ESRGAN超分辨率

## 安装
```bash
pip install -r requirements.txt
```

## 使用方法
```python
import cv2
from image_preprocess.pipeline import ImagePreprocessPipeline

# 初始化处理管道
pipe = ImagePreprocessPipeline(device="cuda")  # 使用GPU加速

# 读取图像
img = cv2.imread("input.jpg")

# 处理图像
result = pipe.process(img)

# 保存结果
cv2.imwrite("output.jpg", result)
```

## 功能实现
### 图像增强
基于RetinexNet实现，包含：
1. 图像分解(DecomNet)
2. 光照调整(EnhanceNet)
3. 反射率恢复(RetinexNet)

### 超分辨率
基于Real-ESRGAN实现，支持:
- 通用图像超分辨率
- 老照片修复

## 涉及技术
1. Retinex理论
2. 深度学习(PyTorch实现)
3. GAN网络(Real-ESRGAN)
4. OpenCV图像处理
