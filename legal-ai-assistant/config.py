# config.py - 配置文件

import os
from dotenv import load_dotenv

load_dotenv()

COOKIE_PREFIX = "legal-ai-assistant"
COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD", "") # 从环境变量中获取cookie密码

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "legal_ai_assistant"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "connection_timeout": 10
}

LLM_CONFIG = {
    "model": "qwen-turbo",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.1,
    "streaming": True
}

VECTOR_STORE_DIR = "./vector_stores"

DOCUMENT_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "text-embedding-v1",
    "supported_types": ["pdf", "docx", "txt"]
}

TYPING_SPEED = 0.05

LEGAL_PROMPT_TEMPLATE = """
⚖️ 你是一个专业的法律审查员。请基于提供的【参考文档】对合同进行深入分析。

【核心指令】
1. 📋 基于文档：你的分析必须完全基于【参考文档】中的内容。
2. 🔍 主动分析：请主动识别合同中可能存在的法律风险、漏洞、不明确条款或潜在问题。
3. ⚠️ 风险提示：对于缺失的关键条款（如违约责任、争议解决方式、保密条款等），请明确指出。
4. 📝 引用溯源：每一个结论都必须标注来源文件名 [文件名]。
5. 💡 提供建议：对于发现的问题，可以提供合理的法律建议。

【参考文档】
{context}

【用户问题】
{question}
"""

NO_DOCUMENT_PROMPT = """
您还没有上传任何文件。
作为一个法律助手，我目前只能回答通用的法律常识。
您的问题是：{user_question}
请告诉我，您是否想了解一般性的法律知识？或者您可以上传文件进行具体分析。
"""

NO_RELEVANT_DOCS_PROMPT = """
我看到您上传了文件，但您的问题似乎与文件内容无关。
这是一个通用的法律回答：{通用回答逻辑}...
"""