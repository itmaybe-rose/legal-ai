# document_processor.py - 文档处理模块

import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from config import DOCUMENT_CONFIG, VECTOR_STORE_DIR
from logger import log_info, log_error, log_debug, log_file_upload

# 处理上传的文件，包括解析、分块、嵌入和存储向量库
'''
incremental: 是否启用增量更新
progress_callback: 进度回调函数，用于更新前端进度条
'''
def process_uploaded_files(uploaded_files, user_id, incremental=True, progress_callback=None):
    if not uploaded_files:
        return None, [], []

    all_docs = [] # 所有解析后的文档
    processed_files = [] # 已处理的文件
    error_messages = [] # 错误信息
    new_files = [] # 新上传的文件
    existing_files = [] # 已存在的文件
    existing_vector_store = None # 已存在的向量库

    user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
    
    if incremental and os.path.exists(user_dir):
        existing_vector_store = load_vector_store(user_id)
        if existing_vector_store:
            existing_files = get_existing_file_names(existing_vector_store)
            log_info(f"检测到已有向量库，包含 {len(existing_files)} 个文件", module='document_processor', user_id=user_id)

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        file_type = file_name.split('.')[-1].lower() # 获取文件类型并转换为小写

        if file_type not in DOCUMENT_CONFIG["supported_types"]: # 检查文件类型是否受支持
            continue

        if incremental and file_name in existing_files: 
            log_debug(f"文件 {file_name} 已存在，跳过", module='document_processor', user_id=user_id)
            continue

        new_files.append(uploaded_file) # 新上传的文件

    if not new_files and incremental: # 没有新上传的文件，且启用增量更新
        return load_vector_store(user_id), existing_files, [] # 返回已存在的向量库

    total_files = len(new_files)
    current_file = 0
    
    for uploaded_file in new_files: 
        current_file += 1
        file_name = uploaded_file.name
        file_type = file_name.split('.')[-1].lower()
        
        if progress_callback:
            progress_callback(f"正在解析文件 {current_file}/{total_files}: {file_name}", 
                            (current_file / total_files) * 50)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
            tmp_file.write(uploaded_file.getvalue()) # 写入临时文件
            tmp_file_path = tmp_file.name

        try:
            if file_type == "pdf":
                loader = PyPDFLoader(tmp_file_path)
            elif file_type == "docx":
                loader = Docx2txtLoader(tmp_file_path)
            elif file_type == "txt":
                loader = TextLoader(tmp_file_path, encoding='utf-8')

            docs = loader.load() # 加载文档

            for doc in docs:
                doc.metadata['source'] = file_name # 添加文件名作为元数据

            all_docs.extend(docs) # 合并所有文档
            processed_files.append(file_name) # 记录已处理的文件

        except Exception as e:
            error_msg = f"📄 {file_name}: {str(e)}"
            error_messages.append(error_msg)
            log_file_upload(file_name, user_id, success=False, error_msg=str(e))
            log_error(f"解析错误: {error_msg}", module='document_processor', user_id=user_id, exception=e)
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    if not all_docs: # 没有解析到任何文档
        if incremental and existing_vector_store:
            return existing_vector_store, existing_files, []
        return None, [], []

    if progress_callback:
        progress_callback("正在切分文档...", 55)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=DOCUMENT_CONFIG["chunk_size"], # 每个文档块的字符数
        chunk_overlap=DOCUMENT_CONFIG["chunk_overlap"], # 文档块之间的重叠字符数
    )
    split_docs = text_splitter.split_documents(all_docs) # 分块文档

    if len(split_docs) == 0:
        if incremental and existing_vector_store:
            return existing_vector_store, existing_files, []
        return None, [], []

    try:
        if progress_callback: # 显示进度条
            progress_callback("正在生成向量嵌入...", 65)
            
        embeddings = DashScopeEmbeddings(model=DOCUMENT_CONFIG["embedding_model"])
        os.makedirs(user_dir, exist_ok=True)

        if incremental and existing_vector_store:
            log_info(f"增量更新模式：添加 {len(new_files)} 个新文件", module='document_processor', user_id=user_id)
            if progress_callback:
                progress_callback("正在增量更新向量库...", 80)
            existing_vector_store.add_documents(split_docs) # 添加新文档
            existing_vector_store.save_local(user_dir) # 保存向量库
            all_files = existing_files + processed_files # 合并所有文件
            for file_name in processed_files:
                log_file_upload(file_name, user_id, success=True)
            if progress_callback:
                progress_callback("完成", 100)
            return existing_vector_store, all_files, error_messages
        else:
            log_info("全新构建模式", module='document_processor', user_id=user_id)
            if progress_callback:
                progress_callback("正在构建向量库...", 80)
            vector_store = FAISS.from_documents(split_docs, embeddings)
            vector_store.save_local(user_dir)
            for file_name in processed_files:
                log_file_upload(file_name, user_id, success=True)
            if progress_callback:
                progress_callback("完成", 100)
            return vector_store, processed_files, error_messages

    except Exception as e:
        log_error(f"向量库构建失败: {e}", module='document_processor', user_id=user_id, exception=e)
        return None, [], []

def get_existing_file_names(vector_store):
    """获取向量库中已有的文件名称列表"""
    if not vector_store:
        return []
    
    file_names = set()
    try:
        for doc in vector_store.docstore._dict.values():
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                file_names.add(doc.metadata['source'])
    except Exception as e:
        log_error(f"获取已有文件名失败: {e}", module='document_processor', exception=e)
    
    return list(file_names)

def remove_files_from_vector_store(vector_store, file_names_to_remove, user_id):
    """
    从向量库中删除指定文件的所有文档
    
    Args:
        vector_store: 向量库对象
        file_names_to_remove: 要删除的文件名列表
        user_id: 用户ID
        
    Returns:
        (updated_vector_store, removed_count)
    """
    if not vector_store or not file_names_to_remove:
        return vector_store, 0
    
    removed_count = 0
    
    try:
        # 找到要保留的文档
        remaining_docs = []
        docs_to_remove = []
        
        for doc_id, doc in vector_store.docstore._dict.items():
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                if doc.metadata['source'] in file_names_to_remove:
                    docs_to_remove.append(doc_id)
                else:
                    remaining_docs.append(doc)
        
        removed_count = len(docs_to_remove)
        
        # 如果没有要删除的，直接返回
        if removed_count == 0:
            return vector_store, 0
        
        # 尝试删除（如果索引支持）
        try:
            # 删除文档
            for doc_id in docs_to_remove:
                if doc_id in vector_store.docstore._dict:
                    del vector_store.docstore._dict[doc_id]
            
            # 删除对应的向量（如果支持delete方法）
            if hasattr(vector_store.index, 'delete'):
                vector_store.index = vector_store.index.delete(
                    ids=docs_to_remove,
                    delete_from_store=True
                )
                
                # 保存更新后的向量库
                user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
                vector_store.save_local(user_dir)
                
                log_info(f"成功从向量库中删除 {removed_count} 个文档（来自 {len(file_names_to_remove)} 个文件）", 
                         module='document_processor', user_id=user_id)
                
                return vector_store, removed_count
            else:
                # 索引不支持删除操作（如IndexFlatL2），重新构建向量库
                log_info(f"索引类型不支持删除，重新构建向量库", 
                         module='document_processor', user_id=user_id)
                
                from langchain_community.embeddings import DashScopeEmbeddings
                from langchain_community.vectorstores import FAISS
                from config import DOCUMENT_CONFIG, VECTOR_STORE_DIR
                
                embeddings = DashScopeEmbeddings(model=DOCUMENT_CONFIG["embedding_model"])
                user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
                
                # 使用保留的文档重新构建向量库
                new_vector_store = FAISS.from_documents(remaining_docs, embeddings)
                new_vector_store.save_local(user_dir)
                
                log_info(f"成功重新构建向量库，保留 {len(remaining_docs)} 个文档", 
                         module='document_processor', user_id=user_id)
                
                return new_vector_store, removed_count
        
        except Exception as e:
            # 删除失败，尝试重新构建
            log_error(f"删除失败，尝试重新构建向量库: {e}", 
                      module='document_processor', user_id=user_id, exception=e)
            
            from langchain_community.embeddings import DashScopeEmbeddings
            from langchain_community.vectorstores import FAISS
            from config import DOCUMENT_CONFIG, VECTOR_STORE_DIR
            
            embeddings = DashScopeEmbeddings(model=DOCUMENT_CONFIG["embedding_model"])
            user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
            
            # 使用保留的文档重新构建向量库
            new_vector_store = FAISS.from_documents(remaining_docs, embeddings)
            new_vector_store.save_local(user_dir)
            
            log_info(f"通过重新构建向量库完成删除，保留 {len(remaining_docs)} 个文档", 
                     module='document_processor', user_id=user_id)
            
            return new_vector_store, removed_count
    
    except Exception as e:
        log_error(f"删除文件失败: {e}", module='document_processor', user_id=user_id, exception=e)
        return vector_store, 0

def clear_all_files(user_id):
    """
    清除用户的所有文件和向量库
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 是否成功
    """
    try:
        user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
        if os.path.exists(user_dir):
            import shutil
            shutil.rmtree(user_dir)
            log_info("已清除所有文件和向量库", module='document_processor', user_id=user_id)
            return True
        return True
    except Exception as e:
        log_error(f"清除文件失败: {e}", module='document_processor', user_id=user_id, exception=e)
        return False

def load_vector_store(user_id):
    try:
        user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
        if not os.path.exists(user_dir):
            return None

        embeddings = DashScopeEmbeddings(model=DOCUMENT_CONFIG["embedding_model"])
        vector_store = FAISS.load_local(user_dir, embeddings, allow_dangerous_deserialization=True)
        return vector_store
    except Exception as e:
        print(f"加载向量库失败: {e}")
        return None

def delete_vector_store(user_id):
    try:
        user_dir = os.path.join(VECTOR_STORE_DIR, str(user_id))
        if os.path.exists(user_dir):
            import shutil
            shutil.rmtree(user_dir)
            return True
        return False
    except Exception as e:
        print(f"删除向量库失败: {e}")
        return False