#!/usr/bin/env python3
"""查看向量库内容的工具脚本"""

import os
from document_processor import load_vector_store, get_existing_file_names

def main():
    # 设置用户ID（根据您的实际用户ID修改）
    user_id = 1
    
    # 加载向量库
    print(f"🔄 正在加载用户 {user_id} 的向量库...")
    vector_store = load_vector_store(user_id)
    
    if not vector_store:
        print("❌ 向量库不存在或加载失败")
        return
    
    # 获取已上传的文件名
    file_names = get_existing_file_names(vector_store)
    print(f"\n📁 已上传的文件列表:")
    for i, name in enumerate(file_names, 1):
        print(f"  {i}. {name}")
    
    # 查看文档块数量
    doc_count = len(vector_store.docstore._dict)
    print(f"\n📄 向量库中文档块数量: {doc_count}")
    
    # 查看向量维度
    dimension = vector_store.index.d
    print(f"📐 向量维度: {dimension}")
    
    # 查看前3个文档内容预览
    print("\n🔍 文档内容预览（前3个）:")
    docs_list = list(vector_store.docstore._dict.items())
    for i, (doc_id, doc) in enumerate(docs_list[:3]):
        source = doc.metadata.get('source', '未知文件')
        content = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
        print(f"\n--- 文档块 {i+1} ---")
        print(f"ID: {doc_id[:10]}...")
        print(f"来源: {source}")
        print(f"内容: {content}")
    
    # 查看最后几个文档
    if len(docs_list) > 3:
        print("\n📋 最后3个文档:")
        for i, (doc_id, doc) in enumerate(docs_list[-3:]):
            source = doc.metadata.get('source', '未知文件')
            content = doc.page_content[:80] + "..." if len(doc.page_content) > 80 else doc.page_content
            print(f"\n--- 文档块 {len(docs_list)-2+i} ---")
            print(f"来源: {source}")
            print(f"内容预览: {content}")

if __name__ == "__main__":
    main()
