# 💊 Drug OCR 药品说明书识别系统

基于 **OCR + 图像增强 + 大模型结构化解析** 的药品说明书智能识别系统。
支持将拍摄的药品包装或说明书图片自动转换为 **结构化说明书文本**，适用于医疗信息检索、用药辅助系统、智能问诊等场景。

---

## 一、项目整体说明

本项目采用 **模块化 AI 工程架构**，将图像增强、OCR 识别、语义结构化解析解耦，形成可复用、可扩展的药品说明书识别服务。

**核心流程：**
```
图片 → 图像增强 → OCR 文字识别 → LLM 语义结构化 → 统一 API 输出
```
---

## 二、目录结构说明

```text
Drug_OCR/
├── app.py                     # FastAPI 入口
├── core/
│   ├── engine.py               # 药品 OCR 核心引擎
│   ├── pipeline.py             # OCR → LLM 推理流水线
│   ├── models.py               # EngineResult 数据结构
│   └── schemas.py              # API Response Schema（Swagger 展示）
├── ocr/
│   └── ocr_engine.py           # RapidOCR 封装
├── ai/
│   └── llm_structured_extractor.py  # 大模型结构化解析
├── config/
│   └── settings.py             # 模型路径 / 参数配置
├── requirements.txt
└── README.md
```

---

## 三、模型与资源准备（重要）

请确保本地模型目录结构如下：

```text
D:\ai_models\
├── real_esrgan\        # 图像超分 / 去模糊
│   └── RealESRGAN_x4plus.pth
├── retinex\            # 低光照增强（RetinexNet）
│   └── retinex_net.pth
└── yolo\               # 文档版面 / 目标检测
    └── doclayout_yolo_best.pt
```

> ⚠️ 注意
>
> * **模型路径在代码中统一配置**
> * 不建议放在 C 盘，避免缓存和权限问题

---

## 四、核心技术说明

### 1️⃣ 图像增强模块

用于提升手机拍摄说明书的可读性：

* **RetinexNet**

  * 低光照环境增强
  * 解决药盒反光、阴影问题
* **Real-ESRGAN**

  * 超分辨率 + 去模糊
  * 提升小字、模糊文字的 OCR 成功率

---

### 2️⃣ OCR 文字识别

* 引擎：**RapidOCR**
* 优点：

  * 中文识别准确率高
  * 推理速度快
  * 支持复杂版式

OCR 模块 **只负责“把字读出来”**，不做语义判断。

---

### 3️⃣ 大模型结构化解析（LLM）

* 输入：OCR 原始文本
* 输出：结构化说明书 JSON

示例结构：

```json
{
  "药品名称": "感冒灵颗粒",
  "功能主治": "...",
  "用法用量": "...",
  "不良反应": "...",
  "注意事项": "..."
}
```

该模块是系统的**智能核心**。

---

### 4️⃣ AI 推理流水线设计

```text
RecognitionPipeline
 ├─ OCR 识别
 ├─ 文本清洗
 ├─ LLM 结构化抽取
 └─ 规整说明书生成
```

流水线与 Web/API 完全解耦，便于：

* CLI 调用
* 批处理
* 后续接数据库 / RAG / 知识图谱

---

## 五、项目启动方式

### ✅ 1️⃣ 创建虚拟环境（推荐）

```bash
conda create -n drug_ocr python=3.10
conda activate drug_ocr
```

或：

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

### ✅ 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

---

### ✅ 3️⃣ 启动服务

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后访问：

* **Swagger 文档**

  ```
  http://127.0.0.1:8000/docs
  ```

---

## 六、API 使用说明

### 🔹 1️⃣ 接口说明

| 项目           | 说明                    |
| ------------ | --------------------- |
| URL          | `/api/recognize`      |
| Method       | `POST`                |
| Content-Type | `multipart/form-data` |
| 参数           | `file`（图片文件）          |

---

### 🔹 2️⃣ 请求示例（curl）

```bash
curl -X POST "http://127.0.0.1:8000/api/recognize" \
  -F "file=@test.jpg"
```

---

### 🔹 3️⃣ 成功响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "drug_name": "感冒灵颗粒",
    "full_text": "【药品名称】\n感冒灵颗粒\n\n【功能主治】...",
    "structured_text": {
      "药品名称": "感冒灵颗粒",
      "功能主治": "...",
      "用法用量": "..."
    },
    "raw_ocr_text": "请仔细阅读说明书...",
    "llm_used": true
  }
}
```

---

### 🔹 4️⃣ 错误返回示例

```json
{
  "code": 1,
  "message": "不支持的图片格式",
  "data": null
}
```

