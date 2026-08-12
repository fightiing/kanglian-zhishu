"""药品说明书文本重整模块，使用大语言模型优化OCR结果

@author: wsy
@date: 2026.01.07
@desc: 提供药品说明书的智能文本重整功能，自动处理OCR识别错误和不规范表达
"""

from typing import Optional, Any, TYPE_CHECKING
from config import LLMConfig

# 类型检查专用导入，避免循环依赖
if TYPE_CHECKING:
    from ai.llm_client import LLMClient


class LLMRewriter:
    """基于大语言模型的药品说明书文本重整器
    
    功能特性:
    - 自动修正OCR识别错误的文本
    - 优化语句结构和表达方式
    - 处理失败时自动降级返回原文本
    - 线程安全，接口简洁
    
    使用注意事项:
    - 需要配置LLMConfig.ENABLE_LLM启用
    - 初始化失败会自动降级为非LLM模式
    """

    def __init__(self):
        """初始化LLM文本重整器
        
        根据配置决定是否启用LLM功能：
        - 如果LLMConfig.ENABLE_LLM为False，直接禁用
        - 否则尝试初始化LLM客户端
        - 初始化失败自动降级为非LLM模式
        """
        self.enable: bool = False  # 是否启用LLM功能
        self.client: Optional[Any] = None  # LLM客户端实例

        # 配置检查
        if not LLMConfig.ENABLE_LLM:
            return

        try:
            from ai.llm_client import LLMClient
            self.client = LLMClient()
            self.enable = True
            print("[LLM] DeepSeek 大模型已启用")
        except Exception as e:
            print(f"[LLM] 初始化失败，自动降级: {e}")
            self.enable = False
            self.client = None

    def rewrite(self, section: str, text: str) -> str:
        """重整药品说明书文本
        
        Args:
            section: 说明书章节名称(如"用法用量")
            text: 待重整的原始文本
            
        Returns:
            str: 重整后的文本，失败时返回原文本
            
        Note:
            - 保证永不抛出异常
            - 过短文本(<20字符)不处理
            - LLM返回空值时回退原文本
        """
        if not self.enable or self.client is None:
            return text

        # 跳过空文本和过短文本
        if not text or len(text.strip()) < 20:
            return text

        try:
            prompt = self._build_prompt(section, text)
            out = self.client.generate(prompt)

            # 处理LLM返回空值的情况
            if not out or not str(out).strip():
                return text

            return str(out).strip()
        except Exception as e:
            print(f"[LLM] 语序矫正失败，已跳过: {e}")
            return text

    def _build_prompt(self, section: str, text: str) -> str:
        """构造LLM提示词
        
        Args:
            section: 说明书章节名称
            text: 待处理的原始文本
            
        Returns:
            str: 格式化后的完整提示词
        """
        return (
            "你是中文【药品说明书】编辑助手。\n\n"
            f"章节：{section}\n\n"
            "要求：\n"
            "- 仅调整语序与措辞,以及不合适通顺的字和词以及错别字，严谨修改\n"
            "- 修复 OCR 语病\n"
            "- 不新增、不删减、不推断医学信息\n"
            "- 可以适当交换不同标签的内容，例如：包装种不出现：口王口苦、腹润、腹痛、腹部不适：皮疹、瘙痒、尊麻疹，而是要写在不良反应中，但保持原意与医学严谨性，\n"
            "- 输出为标准说明书中文\n\n"
            "原文：\n"
            f"{text}\n\n"
            "修订后：\n"
        )
