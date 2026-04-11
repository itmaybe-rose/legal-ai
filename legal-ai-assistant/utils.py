# utils.py - 专门存放工具函数

import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS

def process_uploaded_files(uploaded_files):
    """
    统一处理上传的文件（PDF, DOCX, TXT），返回构建好的向量数据库 (FAISS)
    
    Args:
        uploaded_files: Streamlit file_uploader 返回的文件对象列表
    
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
        vector_store = FAISS.from_documents(split_docs, embeddings)
        return vector_store, processed_files
    except Exception as e:
        print(f"向量库构建失败: {e}")
        return None, []