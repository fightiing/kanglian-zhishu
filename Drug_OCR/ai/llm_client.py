"""大语言模型客户端实现，支持DeepSeek/OpenAI等兼容API

@author: wsy
@date: 2026.01.07
@desc: 提供统一的LLM调用接口，支持多种兼容OpenAI API的大模型服务
"""

import httpx
from config import LLMConfig

# 尝试导入OpenAI模块，失败时使用模拟客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("WARNING: OpenAI模块未安装，使用模拟客户端")
    OPENAI_AVAILABLE = False


class LLMClient:
    """大语言模型客户端封装
    
    功能特性:
    - 支持DeepSeek/OpenAI等兼容API
    - 统一接口规范
    - 可配置模型参数
    
    配置要求:
    - 需在config.py中配置API_KEY/BASE_URL/MODEL
    """

    def __init__(self):
        """初始化LLM客户端
        
        从LLMConfig读取配置创建客户端实例
        """
        # 版本兼容性处理
        self._init_openai_client()
        self.model = LLMConfig.MODEL  # 使用的模型名称

    def _init_openai_client(self):
        """初始化OpenAI客户端，处理版本差异"""
        if not OPENAI_AVAILABLE:
            # OpenAI模块不可用，直接使用模拟客户端
            print("⚠ OpenAI模块不可用，使用模拟客户端")
            self.client = self._create_mock_client()
            return
        
        try:
            # 方式1：标准方式初始化（OpenAI 1.x版本）
            self.client = OpenAI(
                api_key=LLMConfig.API_KEY,  # API访问密钥
                base_url=LLMConfig.BASE_URL,  # API基础地址
            )
            print("✓ OpenAI客户端初始化成功 (标准模式)")
            
        except TypeError as e:
            # 如果报错包含'proxies'，说明是旧版本或配置问题
            if 'proxies' in str(e):
                print(f"⚠ 检测到proxies参数错误: {e}")
                print("尝试使用备选方式初始化...")
                self._init_openai_client_fallback()
            else:
                raise e
    
    def _init_openai_client_fallback(self):
        """备选方式初始化OpenAI客户端"""
        try:
            # 方式2：使用自定义的httpx客户端
            import httpx
            
            # 创建自定义HTTP客户端
            http_client = httpx.Client(
                timeout=60.0,
                # 注意：新版本OpenAI不接受proxies参数，所以不传递
            )
            
            self.client = OpenAI(
                api_key=LLMConfig.API_KEY,
                base_url=LLMConfig.BASE_URL,
                http_client=http_client,
            )
            print("✓ OpenAI客户端初始化成功 (自定义HTTP客户端)")
            
        except Exception as e:
            print(f"✗ 备选方式也失败: {e}")
            # 创建模拟客户端
            self.client = self._create_mock_client()
    
    def _create_mock_client(self):
        """创建模拟客户端（用于调试）"""
        print("⚠ 使用模拟OpenAI客户端")
        
        class MockOpenAIClient:
            def __init__(self):
                self.chat = type('obj', (), {})()
                self.chat.completions = type('obj', (), {})()
                
                def mock_create(**kwargs):
                    class MockResponse:
                        def __init__(self):
                            self.choices = [type('obj', (),
                                {
                                    'message': type('obj', (),
                                        {'content': '这是一个模拟的LLM回复。药品名称：模拟药品，生产厂家：模拟制药'}
                                    )
                                }
                            )]
                    return MockResponse()
                
                self.chat.completions.create = mock_create
        
        return MockOpenAIClient()

    def generate(self, prompt: str) -> str:
        """生成文本内容
        
        Args:
            prompt: 输入的提示词文本
            
        Returns:
            str: 模型生成的文本内容
            
        Note:
            - 使用system prompt限定模型角色
            - temperature=0.2保证输出稳定性
        """
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的中文药品说明书编辑助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # 低随机性保证医学严谨性
            )

            return resp.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM生成失败: {e}")
            # 返回模拟结果
            return f"药品信息提取结果（模拟）：\n药品名称：模拟药品\n生产厂家：模拟制药\n适应症：模拟适应症\n用法用量：请遵医嘱"