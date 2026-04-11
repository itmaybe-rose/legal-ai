# --- 0. 顶部加载环境变量 ---
import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# --- 1. 修改导入路径 (移除了报错的 create_stuff_documents_chain) ---


from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser  # 新增：用于解析字符串
# 注意：不再需要 from langchain.chains.combine_documents import create_stuff_documents_chain
from utils import process_uploaded_files 
# # 1. 引入你的样式模块
# from style import apply_theme
# # 2. 立即应用主题 (放在最前面)
# apply_theme()

# --- 2. Cookie 初始化 (关键：必须在最开始) ---
from streamlit_cookies_manager import EncryptedCookieManager

cookies = EncryptedCookieManager(
    prefix="legal-ai-assistant",
    password="your-super-secret-password" # 必须和 main.py 里的密码一致
)
if not cookies.ready():
    st.stop()

# --- 3. 恢复登录状态 (关键修复) ---
# 如果 Session 里没有，但从 Cookie 读到了，就补回去
if "logged_in" not in st.session_state:
    if cookies.get("logged_in") == "true":
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookies.get("username")

# --- 4. 登录状态检查 (核心保护) ---
if not st.session_state.get("logged_in"):
    st.switch_page("main.py") # 跳回登录页

# 获取当前用户名
current_user = st.session_state.get("username", "用户")

api_key = os.getenv("DASHSCOPE_API_KEY")
#修复模型重复加载(优化性能)
#缓存装饰器，防止每次提问时都重新加载模型导致卡顿
@st.cache_resource
def get_llm():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return None
    return ChatOpenAI(
        model="qwen-turbo",
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.1
    )



 
# --- 2. 页面配置 ---
st.set_page_config(page_title="法律 AI 助手", page_icon="⚖️")
# st.title("⚖ 合同问答助手")

# --- 初始化 Session State (关键修复) ---
# 1. 初始化向量数据库 (vec_store)
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
# 2. 初始化聊天历史 (防止报错)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" in st.session_state:
    st.session_state.user_question = ""
    
with st.sidebar:
   
    
    st.write(f"欢迎, {st.session_state.username}")
    # 退出按钮
    #既安全退出，又不占用服务器资源。
    if st.button("退出登录", use_container_width=True):
        # 1. 清理应用内部缓存 (释放内存，必须做)
        if "vector_store" in st.session_state:
            del st.session_state.vector_store
        if "chat_history" in st.session_state:
            del st.session_state.chat_history
            # 2. 清理登录状态 (内存)
        st.session_state.logged_in = False
        st.session_state.username = None
            # 3. 清理 Cookie
        cookies["logged_in"] = ""
        cookies["username"] = ""
        cookies.save() #保存           
    
        st.success("已退出")
        st.rerun()

    # 文件上传功能
    st.markdown("---")
    st.subheader("📁 文件上传")
    uploaded_files = st.file_uploader(
        "上传文件",
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True,
        key="sidebar_uploader"
    )
    
    # 处理文件上传
    if uploaded_files:
        if 'last_uploaded_files' not in st.session_state or st.session_state.last_uploaded_files != uploaded_files:
            st.session_state.last_uploaded_files = uploaded_files
            
            with st.spinner("正在解析并建立索引..."):
                # 调用 utils.py 中的逻辑
                vector_store, processed_files = process_uploaded_files(uploaded_files)
                
                if vector_store:
                    st.session_state.vector_store = vector_store
                    st.success(f"✅ 已加载: {', '.join(processed_files)}")
                else:
                    st.error("文件处理失败")

            
# --- 5. 主界面：问答 ---
st.title("⚖️ 法律 AI 助手")
 
# 显示聊天历史
st.subheader("聊天历史")
for i, (question, answer) in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(answer)
st.divider()

 
    # 聊天输入框
 
user_question = st.chat_input("请输入关于文档的问题：",key="chat_input")

# B. 处理用户问题
if user_question:
        # 显示用户问题
    with st.chat_message("user"):
        st.write(user_question)

    if not api_key:
        with st.chat_message("assistant"):
            st.warning("请设置 DASHSCOPE_API_KEY 环境变量以生成回答。")
    else:
        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考..."):
                try:
                    # 1. 设置 LLM 调用模型
                    llm = get_llm()
                    if not llm:
                        st.error("无法加载模型，请检查环境变量设置。")
                        st.stop()
                                
                    if st.session_state.vector_store:
                    # 3. 检索文档
                        retrieved_docs = st.session_state.vector_store.similarity_search(user_question)
                    
                    # 4. 格式化 Context
                        context_text = ""
                        for doc in retrieved_docs:
                            # 只显示文件名，不显示页码
                            source = doc.metadata.get("source", "未知文件")
                            context_text += f"[来源: {source}]\n"
                            context_text += doc.page_content + "\n\n---\n\n"

                        # 5. 构建最终链
                        # 2. 定义提示词模板
                        template = """
你是一个文档问答助手。请根据以下已知信息回答用户的问题。
已知信息：
{context}

**重要要求：**
1. 回答必须基于已知信息，不要编造。
2. **必须在回答中引用来源文件名**，格式为 [文件名]。
3. **每个关键信息点都要标注来源文件名**，确保用户知道信息来自哪个文件。
4. 不要编造任何信息，只基于已知信息回答。
5. **即使信息来自同一个文件，也要在每个关键信息点后标注文件名**。
6. **文件名必须与已知信息中显示的文件名完全一致**，不要修改或简化文件名。

问题：
{question}
"""
                        prompt = ChatPromptTemplate.from_template(template)
                        rag_chain = prompt | llm | StrOutputParser()

                        # 6. 调用链
                        response = rag_chain.invoke({
                            "context": context_text, 
                            "question": user_question
                        })
                    else:
                         # --- 情况 B：没有文档，走通用对话流程 ---
                        # 这里可以设置一个通用的 Prompt，告诉 AI 没有文档上下文
                        generic_template = """你是一个法律AI助手。当前还没有上传任何合同文档。
                        请回答用户的一般性问题，或者提示用户上传文档以便进行具体的合同问答。
                        
                        用户的问题：{question}"""
                        
                        prompt = ChatPromptTemplate.from_template(generic_template)
                        chain = prompt | llm | StrOutputParser()
                        response = chain.invoke({"question": user_question})
                    # 显示 AI 回答
                    st.markdown(response)

                    # 将对话添加到历史记录
                    st.session_state.chat_history.append((user_question, response))

                except Exception as e:
                    st.error(f"发生错误: {e}")

