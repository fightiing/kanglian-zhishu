# 康联智枢——面向主动健康的知识驱动医疗智能协同网络

> 基于 **知识图谱 + RAG 检索增强生成 + DeepSeek 大模型** 的智能医疗健康协同服务平台
> 采用**五层架构**设计，融合语音交互、药品识别 OCR、医生推荐、健康档案管理等核心能力

---

## 项目简介

**康联智枢**是一个面向主动健康的知识驱动型医疗智能协同网络平台，通过将医疗知识图谱、检索增强生成（RAG）与大语言模型深度耦合，为社区与家庭场景提供智能疾病咨询、用药安全辅助、语音健康问答、药品识别与医生推荐等一体化服务，助力家庭-医疗协同的主动健康管理。

### 核心能力

| 能力 | 实现 | 模块 |
|---|---|---|
| 医疗知识图谱 | 500+ 疾病、8 类节点、10,000+ 关系 | 数据层 |
| 检索增强生成（RAG） | 基于 Cypher 的多跳知识检索 | 检索层 |
| 大模型智能问答 | DeepSeek API / Ollama 本地双模式 | 生成层 |
| 语音健康咨询 | 百度 ASR + TTS 全双工语音交互 | 基础设施层 |
| 药品智能识别 | 图像增强 + YOLO 布局检测 + OCR + LLM 结构化抽取 | Drug_OCR 模块 |
| 医生推荐 | 症状匹配 + LangChain + Neo4j 增强 | 应用层 |
| 健康档案管理 | 个人/共享档案、用药依从性跟踪 | 应用层 |
| 知识图谱可视化 | Neo4j 原生图形展示 | 应用层 |

---

## 📁 五层架构

```
康联智枢/
├── 0_infrastructure/         基础设施层
│   ├── config.py            # 全局配置（百度AI/Neo4j/Ollama）
│   ├── langchain_config.py  # LangChain + Neo4j 配置
│   ├── asr_service.py       # 语音识别（百度ASR）
│   ├── tts_service.py       # 语音合成（百度TTS）
│   └── audio_converter.py   # 音频格式转换
│
├── 1_data_layer/            数据层
│   └── kg_builder.py        # 医疗知识图谱构建（导入 medical.json）
│
├── 2_retrieval_layer/       检索层
│   └── rag_retriever.py     # RAG 知识检索器
│
├── 3_generation_layer/      生成层
│   └── llm_generator.py     # DeepSeek 大模型（API + Ollama 双模式）
│
├── 4_application_layer/     应用层
│   ├── web_app/             # Flask Web 服务（主入口）
│   │   ├── app.py
│   │   ├── templates/       # 7 个 PWA 页面
│   │   └── static/          # PWA 资源
│   ├── app_interface/       # 命令行交互入口
│   ├── doctor_recommend/    # 医生推荐子系统
│   └── health_record/       # 健康档案管理
│
├── Drug_OCR/                药品识别模块（独立子系统）
│   ├── api/                 # Flask API 接口
│   ├── core/                # 识别引擎
│   ├── image_preprocess/    # 图像增强（Retinex + Real-ESRGAN）
│   ├── layout/              # YOLO 布局检测
│   ├── ocr/                 # OCR 引擎
│   ├── extractor/           # 知识抽取
│   └── ai/                  # LLM 客户端
│
├── docs/                    模块开发文档
├── medical.json             医疗数据源（500+ 疾病）
├── doctor.csv               医生信息数据
├── requirements.txt         Python 依赖
├── Procfile                 云端部署启动命令（Render/Railway）
├── run_server.py            生产 WSGI 入口（waitress）
├── import_cloud_neo4j.py    # 云端 Neo4j 一键导入脚本
└── README.md                本文档
```

---

## 🚀 快速开始

### 一、本地开发运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 启动 Neo4j 数据库

```bash
neo4j.bat console          # Windows
# 或 neo4j start           # Linux/Mac
```

默认地址 `bolt://localhost:7687`，初始密码 `neo4j`。

#### 3. 构建知识图谱

```bash
cd 1_data_layer
python kg_builder.py
```

会将 `medical.json` 中 500 条疾病数据导入 Neo4j。

#### 4. 启动 Web 服务

```bash
cd 4_application_layer/web_app
python app.py
```

访问 http://localhost:8080 即可使用。

#### 5.（可选）启动 Ollama 本地大模型

```bash
ollama serve
ollama pull deepseek-r1:7b
```

> 未启动 Ollama 时，系统会自动回退到 DeepSeek API 模式（需配置 `DEEPSEEK_API_KEY`）。

---

### 二、云端部署（推荐用于比赛/演示）

支持 **Render.com + Neo4j AuraDB** 的免费云端部署方案，可获得 24/7 公网访问链接。

#### 1. 创建云端 Neo4j AuraDB 实例

- 访问 https://console.neo4j.io 注册并创建 Free 实例
- 保存 `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD`

#### 2. 一键导入知识图谱到云端

```powershell
$env:NEO4J_URI="neo4j+s://xxxxxxxx.databases.neo4j.io"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="你的AuraDB密码"
python import_cloud_neo4j.py
```

#### 3. 部署到 Render.com

- 推送代码到 GitHub 公开仓库
- 在 Render 创建 Web Service，配置：
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `waitress-serve --host=0.0.0.0 --port=$PORT --threads=8 run_server:app`
- 添加环境变量：`NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` / `DEEPSEEK_API_KEY`

部署成功后获得形如 `https://康联智枢.onrender.com` 的公网访问链接。

---

## 🎯 核心功能

### 1. 智能疾病咨询
基于知识图谱的多跳检索 + DeepSeek 大模型生成，提供疾病症状、用药、饮食、检查项目等结构化健康建议。

### 2. 语音健康问答
全双工语音交互：百度 ASR 识别用户语音提问 → RAG 检索 → LLM 生成答复 → 百度 TTS 语音播报，适合老年用户。

### 3. 药品智能识别
拍照识别药品包装：图像增强（Retinex + Real-ESRGAN）→ YOLO 布局检测 → OCR 文字识别 → LLM 结构化抽取 → 知识图谱比对，输出药品名称、规格、用法用量及用药安全提示。

### 4. 医生推荐
基于症状匹配的医生推荐系统，结合 LangChain 与 Neo4j 增强查询，按科室、距离、专长智能排序。

### 5. 健康档案管理
个人健康档案 CRUD、家庭共享档案、用药依从性跟踪与报告生成。

### 6. 知识图谱可视化
原生 Neo4j 图形展示，支持节点过滤、关系遍历、疾病关联查询。

---

## 🔧 技术栈

| 层级 | 技术栈 | 用途 |
|---|---|---|
| **基础设施层** | 百度 AI（TTS/ASR/OCR）、音频处理库 | 语音交互、图像识别 |
| **数据层** | Neo4j + py2neo + Cypher | 知识图谱存储与构建 |
| **检索层** | Cypher 多跳查询 | RAG 知识检索 |
| **生成层** | DeepSeek API / Ollama 本地部署 | 智能问答生成 |
| **应用层** | Flask + Jinja2 + PWA | Web 应用、命令行交互 |
| **药品识别** | OpenCV + YOLO + RapidOCR + Real-ESRGAN | 端到端 OCR Pipeline |
| **部署** | waitress + Render + AuraDB | 生产级云端部署 |

---

## 📊 系统规模

- **医疗数据**：500+ 疾病，10,000+ 知识图谱关系
- **节点类型**：疾病、症状、并发症、科室、治疗方式、检查项目、药物、食物
- **关系类型**：症状表现、推荐药物、常用药物、宜吃、忌吃、就诊科室、需要检查等
- **Web 页面**：7 个 PWA 适配页面（首页、知识图谱、医生推荐、药品识别、语音咨询、健康档案、共享档案）

---

## 🧪 测试

项目根目录下提供多个功能验证脚本：

| 脚本 | 用途 |
|---|---|
| `test_asr.py` / `test_asr_simple.py` | 百度 ASR 语音识别验证 |
| `test_recording_save.py` / `verify_recording_save.py` | 录音保存验证 |
| `test_fixed_asr.py` / `validate_asr_with_real_audio.py` | ASR 准确性验证 |
| `final_verification.py` / `improve_asr_accuracy.py` | 综合准确性提升 |
| `4_application_layer/web_app/test_*.py` | 各功能模块单元测试 |

详细测试说明请参见 [测试说明.md](测试说明.md)。

---

## 🌐 部署架构

### 本地架构

```
[浏览器] ──> Flask (8080) ──> RAG检索 ──> Neo4j (7687)
                  │              │
                  ├──> DeepSeek LLM
                  ├──> 百度 TTS/ASR
                  └──> Drug_OCR Pipeline
```

### 云端架构

```
[公网] ──> Render.com (waitress WSGI) ──> RAG ──> Neo4j AuraDB (neo4j+s)
                  │                          │
                  ├──> DeepSeek API           └── 数据持久化
                  ├──> 百度 TTS/ASR
                  └──> Drug_OCR Pipeline
```

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v3.0 | 2026-08-12 | 适配云端部署，新增 waitress 生产入口、AuraDB 一键导入脚本、统一项目命名为「康联智枢」 |
| v2.0 | 2026-01-06 | 五层架构重构，分离基础设施层 |
| v1.0 | 2026-01-05 | 初始版本，完成知识图谱 + RAG + LLM 集成 |

---

## 📜 许可证

本项目仅供学习与比赛使用。

---

## 📞 联系方式

- **项目维护**：康联智枢开发小组
- **最后更新**：2026-08-12
- **架构版本**：v3.0（云端部署就绪）
