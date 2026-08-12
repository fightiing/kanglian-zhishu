from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil
from pathlib import Path

from core.engine import DrugOCREngine
from core.schemas import DrugOCRResponse

app = FastAPI(title="Drug OCR API", version="1.0")

# ===== 允许前端跨域（开发阶段必须）=====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DrugOCREngine()


@app.post(
    "/api/recognize",
    response_model=DrugOCRResponse,
    summary="识别药品说明书",
    description="上传药品说明书图片，返回 OCR + LLM 结构化结果"
)
async def recognize_drug_manual(file: UploadFile = File(...)):
    """
    药品说明书识别接口
    """
    if not file.filename:
        return _error("未上传文件")

    # 1️⃣ 保存临时文件
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        return _error("不支持的图片格式")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        image_path = tmp.name

    # 2️⃣ 调用核心引擎
    try:
        result = engine.recognize(image_path)
    except Exception as e:
        return _error(f"识别失败: {str(e)}")
    finally:
        Path(image_path).unlink(missing_ok=True)

    # 3️⃣ 返回统一结构
    return {
        "code": 0,
        "message": "success",
        "data": {
            "drug_name": result.drug_name,
            "full_text": result.full_text,
            "structured_text": result.structured_text,
            "raw_ocr_text": result.raw_ocr_text,
            "llm_used": result.llm_used,
        }
    }


def _error(msg: str):
    return {
        "code": 1,
        "message": msg,
        "data": None
    }
