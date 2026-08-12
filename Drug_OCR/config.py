# """项目配置文件，管理所有模型和API的配置

# @author: wsy
# @date: 2026.01.07
# @desc: 集中管理环境变量和模型路径配置，提供必要的工具函数
# """

# import os
# from dotenv import load_dotenv

# # 加载.env文件中的环境变量

# load_dotenv()

# # =========================
# # 模型根目录（默认 C 盘兜底）
# # =========================
# MODEL_HOME = os.getenv(
#     "MODEL_HOME",
#     os.path.expanduser("~/.models")
# )

# # =========================
# # RetinexNet
# # =========================
# RETINEX_WEIGHT = os.path.join(
#     MODEL_HOME,
#     os.getenv("RETINEX_WEIGHT")
# )

# # =========================
# # Real-ESRGAN
# # =========================
# REAL_ESRGAN_WEIGHT = os.path.join(
#     MODEL_HOME,
#     os.getenv("REAL_ESRGAN_WEIGHT")
# )

# REAL_ESRGAN_URL = os.getenv("REAL_ESRGAN_URL")


# def ensure_dirs():
#     """确保模型目录存在"""
#     for p in [RETINEX_WEIGHT, REAL_ESRGAN_WEIGHT]:
#         if p is None:
#             continue
#         os.makedirs(os.path.dirname(p), exist_ok=True)
#         print(f"[OK] Ensure dir: {os.path.dirname(p)}")

# DocLayout_YOLO = os.path.join(
#     MODEL_HOME,
#     os.getenv("DocLayout_YOLO")
# )

# class LLMConfig:
#     """大语言模型配置类
    
#     配置项说明:
#     - ENABLE_LLM: 是否启用LLM功能(默认False)
#     - PROVIDER: 模型提供商(deepseek/openai等)
#     - API_KEY: API访问密钥
#     - BASE_URL: API基础地址
#     - MODEL: 使用的模型名称
#     - TIMEOUT: 请求超时时间(秒)
#     """
#     ENABLE_LLM = os.getenv("ENABLE_LLM", "0") == "1"  # 是否启用LLM功能
#     PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # 模型提供商
#     API_KEY = os.getenv("LLM_API_KEY", "")  # API密钥
#     BASE_URL = os.getenv("LLM_BASE_URL", "")  # API基础地址
#     MODEL = os.getenv("LLM_MODEL", "deepseek-chat")  # 模型名称
#     TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))  # 超时时间(秒)

#     TIMEOUT = 60  # 固定超时时间为60秒

# for k, v in os.environ.items():
#     if k.startswith("LLM_"):
#         print(f"{k}={v}")

# ensure_dirs()
"""项目配置文件，管理所有模型和API的配置

@author: wsy
@date: 2026.01.07
@desc: 集中管理环境变量和模型路径配置，提供必要的工具函数
"""

import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# =========================
# 模型根目录（默认 C 盘兜底）
# =========================
MODEL_HOME = os.getenv(
    "MODEL_HOME",
    os.path.expanduser("~/.models")
)

# =========================
# RetinexNet
# =========================
RETINEX_WEIGHT = os.path.join(
    MODEL_HOME,
    os.getenv("RETINEX_WEIGHT", "")  # 补充默认空字符串，避免拼接出无效路径
)

# =========================
# Real-ESRGAN
# =========================
REAL_ESRGAN_WEIGHT = os.path.join(
    MODEL_HOME,
    os.getenv("REAL_ESRGAN_WEIGHT", "")
)

REAL_ESRGAN_URL = os.getenv("REAL_ESRGAN_URL", "")

# =========================
# DocLayout YOLO
# =========================
DocLayout_YOLO = os.path.join(
    MODEL_HOME,
    os.getenv("DocLayout_YOLO", "")
)

# =========================
# 大语言模型配置类
# =========================
class LLMConfig:
    """大语言模型配置类
    
    配置项说明:
    - ENABLE_LLM: 是否启用LLM功能(默认False)
    - PROVIDER: 模型提供商(deepseek/openai等)
    - API_KEY: API访问密钥
    - BASE_URL: API基础地址
    - MODEL: 使用的模型名称
    - TIMEOUT: 请求超时时间(秒)
    """
    ENABLE_LLM = os.getenv("ENABLE_LLM", "0") == "1"  # 是否启用LLM功能
    PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # 模型提供商
    API_KEY = os.getenv("LLM_API_KEY", "")  # API密钥
    BASE_URL = os.getenv("LLM_BASE_URL", "")  # API基础地址
    MODEL = os.getenv("LLM_MODEL", "deepseek-chat")  # 模型名称
    TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))  # 修正：保留环境变量配置，默认值改为60（不再重复赋值）

# =========================
# 工具函数：确保模型目录存在
# =========================
def ensure_dirs():
    """确保模型目录存在"""
    # 整理需要检查的路径列表，过滤空路径
    model_paths = [p for p in [RETINEX_WEIGHT, REAL_ESRGAN_WEIGHT, DocLayout_YOLO] if p]
    for p in model_paths:
        dir_path = os.path.dirname(p)
        os.makedirs(dir_path, exist_ok=True)
        print(f"[OK] Ensure dir: {dir_path}")

# =========================
# 核心需求：打印所有配置变量
# =========================
def print_all_configs():
    """打印所有项目配置变量，分模块展示，提升可读性"""
    print("=" * 80)
    print("【1. LLM_开头环境变量（原始环境变量）】")
    print("-" * 40)
    # 保留原有LLM_开头环境变量打印，优化格式
    llm_env_vars = {k: v for k, v in os.environ.items() if k.startswith("LLM_")}
    if llm_env_vars:
        for k, v in llm_env_vars.items():
            print(f"{k} = {v}")
    else:
        print("无LLM_开头的环境变量")

    print("\n【2. 全局模型配置变量】")
    print("-" * 40)
    # 整理全局配置变量（用字典收纳，方便循环打印，扩展性更强）
    global_configs = {
        "MODEL_HOME": MODEL_HOME,
        "RETINEX_WEIGHT": RETINEX_WEIGHT,
        "REAL_ESRGAN_WEIGHT": REAL_ESRGAN_WEIGHT,
        "REAL_ESRGAN_URL": REAL_ESRGAN_URL,
        "DocLayout_YOLO": DocLayout_YOLO
    }
    for k, v in global_configs.items():
        print(f"{k} = {v}")

    print("\n【3. LLMConfig类配置属性】")
    print("-" * 40)
    # 打印LLMConfig类的所有配置属性（反射获取，无需手动添加新增属性）
    llm_class_attrs = [attr for attr in dir(LLMConfig) if not attr.startswith("__")]
    for attr in llm_class_attrs:
        attr_value = getattr(LLMConfig, attr)
        print(f"LLMConfig.{attr} = {attr_value}")

    print("=" * 80 + "\n")

# =========================
# 执行操作：打印配置 + 确保目录存在
# =========================
if __name__ == "__main__":
    # 1. 打印所有配置
    print_all_configs()
    # 2. 确保模型目录存在
    ensure_dirs()