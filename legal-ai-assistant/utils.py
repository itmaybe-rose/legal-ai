# utils.py - 专门存放工具函数

import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS

# 定义一个全局的向量库存储根目录
VECTOR_STORE_DIR = "./vector_stores"

def process_uploaded_files(uploaded_files, user_id):
    """
    修改：增加 user_id 参数，实现用户数据隔离

    统一处理上传的文件（PDF, DOCX, TXT），返回构建好的向量数据库 (FAISS)
    
    Args:
        uploaded_files: Streamlit file_uploader 返回的文件对象列表
        user_id: 当前用户的 ID (用于生成唯一的存储路径)
    
    Returns:
        FAISS: 构建好的向量数据库，如果失败返回 None
    """
    if not uploaded_files:
        return None, []

    all_docs = []
    processed_files = []

    for uploaded_file in uploaded_files:
        file_type = uploaded_file.name.split('.')[-1].lower()
        # 使用 tempfile 安全保存文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            if file_type == "pdf":
                loader = PyPDFLoader(tmp_file_path)
                docs = loader.load()
            elif file_type == "docx":
                loader = Docx2txtLoader(tmp_file_path)
                docs = loader.load()
            elif file_type == "txt":
                loader = TextLoader(tmp_file_path, encoding='utf-8')
                docs = loader.load()
            else:
                continue # 跳过不支持的格式

            # 统一处理 Metadata (文件名)
            for doc in docs:
                doc.metadata['source'] = uploaded_file.name
            all_docs.extend(docs)
            processed_files.append(uploaded_file.name)

        except Exception as e:
            print(f"解析 {uploaded_file.name} 时出错: {e}")
        finally:
            # 确保临时文件被清理
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    if not all_docs:
        return None, []

    # 2. 文本切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    split_docs = text_splitter.split_documents(all_docs)

    if len(split_docs) == 0:
        return None, []

    # 3. 创建向量库
    try:
        embeddings = DashScopeEmbeddings(model="text-embedding-v1")
        # ✅ 关键修改 1：如果该用户已有向量库，先加载再添加，否则新建
        # 构建该用户的专属路径
        user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True) # 确保目录存在
        
        # 检查是否已有索引文件
        index_path = os.path.join(user_dir, "index.faiss")
        
        if os.path.exists(index_path):
            # 如果存在，加载旧的库
            vector_store = FAISS.load_local(user_dir, embeddings, allow_dangerous_deserialization=True)
            # 添加新文档
            vector_store.add_documents(split_docs)
        else:
            # 如果不存在，创建新的
            vector_store = FAISS.from_documents(split_docs, embeddings)
        
        # ✅ 关键修改 2：保存到硬盘 (持久化)
        # 这一步是核心，它把数据写进了服务器硬盘
        vector_store.save_local(user_dir)
        return vector_store, processed_files
        
    except Exception as e:
        print(f"向量库构建失败: {e}")
        return None, []