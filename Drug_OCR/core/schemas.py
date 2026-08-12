from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DrugOCRData(BaseModel):
    drug_name: Optional[str] = Field(None, description="药品名称")
    full_text: str = Field(..., description="规整后的完整说明书文本")
    structured_text: Dict[str, Any] = Field(..., description="结构化说明书内容")
    raw_ocr_text: str = Field(..., description="OCR 原始文本")
    llm_used: bool = Field(..., description="是否使用了大模型结构化")


class DrugOCRResponse(BaseModel):
    code: int = Field(..., example=0)
    message: str = Field(..., example="success")
    data: Optional[DrugOCRData]
