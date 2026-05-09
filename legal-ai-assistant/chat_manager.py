# chat_manager.py - 聊天管理模块

import streamlit as st
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import LLM_CONFIG, LEGAL_PROMPT_TEMPLATE, NO_DOCUMENT_PROMPT, NO_RELEVANT_DOCS_PROMPT, TYPING_SPEED
from input_validator import validate_user_input, sanitize_input
from logger import log_info, log_error, log_debug, log_chat_request

def get_llm():
    import os
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        api_key=api_key,
        **LLM_CONFIG # 从配置文件中获取模型参数
       
    )

def format_chat_history(history, max_turns=5):
    if not history:
        return "无历史对话"

    lines = []
    for q, a in history[-max_turns:]:
        lines.append(f"用户: {q}")
        lines.append(f"AI: {a}")

    return "\n".join(lines)

# 格式化检索到的文档内容
def format_context(retrieved_docs):
    context_text = ""
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "未知文件")
        context_text += f"[来源: {source}]\n"
        context_text += doc.page_content + "\n\n---\n\n"
    return context_text

def process_user_question(user_question, vector_store, chat_history, llm, api_key, user_id=None):
    if not api_key:
        log_error("DASHSCOPE_API_KEY 环境变量未设置", module='chat_manager', user_id=user_id)
        return None, "请设置 DASHSCOPE_API_KEY 环境变量以生成回答。"

    is_valid, cleaned_input, error_msg = validate_user_input(user_question) # 验证用户输入
    if not is_valid:
        log_chat_request(user_id, len(user_question), success=False, error_msg=error_msg) # 记录无效输入日志
        return None, error_msg
    
    sanitized_input = sanitize_input(cleaned_input)
    log_info(f"处理用户问题，长度: {len(sanitized_input)} 字符", module='chat_manager', user_id=user_id)

    if not vector_store:
        log_debug("无向量库，使用无文档模式", module='chat_manager', user_id=user_id)
        result = process_without_document(sanitized_input, llm)
        log_chat_request(user_id, len(sanitized_input), success=True)
        return result

    retrieved_docs = vector_store.similarity_search(sanitized_input)
    log_info(f"检索到 {len(retrieved_docs)} 条相关文档", module='chat_manager', user_id=user_id)

    if retrieved_docs:
        result = process_with_document(sanitized_input, retrieved_docs, chat_history, llm)
        log_chat_request(user_id, len(sanitized_input), success=True)
        return result
    else:
        result = process_no_relevant_docs(llm)
        log_chat_request(user_id, len(sanitized_input), success=True)
        return result

# 无文档模式处理
def process_without_document(user_question, llm): 
    prompt = ChatPromptTemplate.from_template(NO_DOCUMENT_PROMPT)
    chain = prompt | llm | StrOutputParser()

    response_container = st.empty()
    final_response = ""

    for chunk in chain.stream({"user_question": user_question}):
        final_response += chunk
        response_container.markdown(final_response) 
        time.sleep(TYPING_SPEED)

    return final_response, None

# 无相关文档模式处理
def process_no_relevant_docs(llm): 
    prompt = ChatPromptTemplate.from_template(NO_RELEVANT_DOCS_PROMPT)
    chain = prompt | llm | StrOutputParser()

    response_container = st.empty()
    final_response = ""

    for chunk in chain.stream({}):
        final_response += chunk
        response_container.markdown(final_response)
        time.sleep(TYPING_SPEED)

    return final_response, None

# 有相关文档模式处理
def process_with_document(user_question, retrieved_docs, chat_history, llm): 
    context_text = format_context(retrieved_docs) # 格式化文档内容
    formatted_history = format_chat_history(chat_history) # 格式化历史对话

    prompt = ChatPromptTemplate.from_template(LEGAL_PROMPT_TEMPLATE)
    rag_chain = prompt | llm | StrOutputParser()

    response_container = st.empty()
    final_response = ""

    for chunk in rag_chain.stream({
        "context": context_text,
        "question": user_question,
        "chat_history": formatted_history
    }):
        final_response += chunk
        response_container.markdown(final_response)
        time.sleep(TYPING_SPEED)

    return final_response, retrieved_docs