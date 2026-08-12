from typing import Union
from pathlib import Path

from core.pipeline import RecognitionPipeline
from core.models import EngineResult


class DrugOCREngine:
    """
    ⭐ 药品说明书识别核心引擎
    - 与 Web / API / DB 完全解耦
    """

    def __init__(self):
        self.pipeline = RecognitionPipeline()

    def recognize(self, image: Union[str, Path]) -> EngineResult:
        image_path = str(image)
        return self.pipeline.run(image_path)
