"""
向量数据库模块：使用 LangChain + FAISS + 本地嵌入模型
"""
import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from utils.logger import logger

# --- 全局配置 ---
# 这里使用一个轻量级的中文嵌入模型，避免下载巨大的英文模型
# 如果你没有模型文件，它会自动从 HuggingFace 下载（第一次运行需要网络）
MODEL_NAME = r"D:\Huggingface" 

# 持久化存储路径
PERSIST_DIR = "./faiss_vector_db"

# 初始化 Embeddings 对象
embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={
        "device": "cpu",           # 或者是 "cuda" 如果你有显卡
        "trust_remote_code": True, # ✅ 放在这里
        "local_files_only": True   # ✅ 放在这里
    }

)

# 全局向量数据库实例
vector_db = None

class VectorDatabase:
    """向量数据库类（基于 LangChain FAISS）"""
    
    def __init__(self):
        self.db = None # LangChain FAISS 实例
        self.documents = [] # 用于存储原始文本（可选）
        self._load_from_disk()
        logger.info("初始化成功，使用 LangChain FAISS")

    def _load_from_disk(self):
        """从磁盘加载向量数据库"""
        if os.path.exists(PERSIST_DIR):
            try:
                self.db = FAISS.load_local(
                    PERSIST_DIR, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info("从磁盘加载成功")
            except Exception as e:
                logger.error(f"加载失败: {e}")
                self.db = None

    def _save_to_disk(self):
        """保存向量数据库到磁盘"""
        if self.db and PERSIST_DIR:
            try:
                self.db.save_local(PERSIST_DIR)
                logger.info("保存到磁盘成功")
            except Exception as e:
                logger.error(f"保存失败: {e}")

    def add_documents(self, documents: List[str]):
        """添加文档（自动向量化）"""
        if not documents:
            return
            
        # 使用 LangChain 的 FAISS.from_texts 直接创建或更新索引
        # 如果 db 已存在，就用 add_texts 添加；否则创建新的
        if self.db is None:
            self.db = FAISS.from_texts(documents, embeddings)
        else:
            self.db.add_texts(documents)
            
        self.documents.extend(documents)
        logger.info(f"成功添加 {len(documents)} 个文档")
        
        # 保存到磁盘
        self._save_to_disk()

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """搜索（真·向量搜索）"""
        if self.db is None or not self.documents:
            logger.warning("警告：数据库为空")
            return []

        # LangChain 的 similarity_search 直接返回最相似的文本
        docs = self.db.similarity_search(query, k=top_k)
        
        # 提取文本内容
        results = [doc.page_content for doc in docs]
        logger.info(f"搜索完成，返回 {len(results)} 个结果")
        return results

    def clear(self):
        """清空数据库"""
        self.db = None
        self.documents = []
        # 删除磁盘上的文件
        if os.path.exists(PERSIST_DIR):
            import shutil
            shutil.rmtree(PERSIST_DIR)
        logger.info("已清空")
    
    def remove_by_keyword(self, keyword: str) -> int:
        """根据关键词删除文档"""
        if not self.documents:
            return 0
        
        # 找出包含关键词的文档索引
        to_remove = [i for i, doc in enumerate(self.documents) if keyword in doc]
        
        if not to_remove:
            logger.info(f"未找到包含关键词 '{keyword}' 的文档")
            return 0
        
        # 保留不包含关键词的文档
        new_docs = [doc for i, doc in enumerate(self.documents) if i not in to_remove]
        removed_count = len(self.documents) - len(new_docs)
        
        # 重新创建索引
        if new_docs:
            self.db = FAISS.from_texts(new_docs, embeddings)
            self.documents = new_docs
        else:
            self.db = None
            self.documents = []
        
        self._save_to_disk()
        logger.info(f"已删除 {removed_count} 个包含关键词 '{keyword}' 的文档")
        return removed_count

# --- 全局实例与工厂函数 ---
def get_vector_db():
    """获取单例"""
    global vector_db
    if vector_db is None:
        vector_db = VectorDatabase()
    return vector_db

# --- 测试 ---
if __name__ == "__main__":
    db = get_vector_db()
    db.add_documents([
        "Java后端开发需要学习Spring Boot和MySQL。",
        "前端开发需要掌握Vue.js和React框架。",
        "Python数据分析需要学习Pandas和NumPy。"
    ])
    
    results = db.search("我想做网页开发，需要学什么？")
    print("搜索结果：", results)