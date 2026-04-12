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

import mysql.connector
from mysql.connector import Error 
import mysql.connector
from mysql.connector import Error 
from langchain_community.embeddings import DashScopeEmbeddings # ✅ 修复向量库错误
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

# --- 1. 数据库连接 (建议放在一个单独的 db.py 或这里) ---
def get_db_connection():
    # 这里复用 main.py 的逻辑，或者直接复制过来
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "legal_ai_assistant"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            connection_timeout=10
        )
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

# --- 2. 核心修改：获取 User ID ---
# 这是连接“登录逻辑”和“存储逻辑”的桥梁
def get_user_id(username):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    return None

# --- 4. 登录状态检查 (核心保护) ---
if not st.session_state.get("logged_in"):
    st.switch_page("main.py") # 跳回登录页

# 获取当前用户名
current_username = st.session_state["username"]
user_id = get_user_id(current_username)
if not user_id:
    st.error("用户身份验证失败，请重新登录")
    st.stop()

# --- 4. 初始化聊天历史：从 MySQL 加载 ---
# 检查 session_state 中是否有历史，如果没有，去数据库捞
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # 🔑 核心：只查这个 user_id 的数据
        cursor.execute(
            "SELECT role, content FROM chat_logs WHERE user_id = %s ORDER BY timestamp ASC", 
            (user_id,)
        )
        rows = cursor.fetchall()
        # 将数据库记录转换为 Streamlit 可用的格式 [(question, answer), ...]
        # 注意：这里简单按顺序配对，实际生产环境建议存对话轮次 ID
        temp_hist = []
        for row in rows:
            temp_hist.append((row[1], "") if row[0] == "user" else ("", row[1]))
        
        # 简单的配对逻辑（实际项目建议优化存储结构）
        for i in range(0, len(temp_hist)-1, 2):
            if i+1 < len(temp_hist):
                st.session_state.chat_history.append((temp_hist[i][0], temp_hist[i+1][1]))
        conn.close()

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

# --- 2.1 智能初始化向量数据库：优先从硬盘恢复 (长期记忆的核心) ---
# 这段代码替换了原来的简单初始化

# 构建该用户的向量库路径 (必须和 utils.py 里的路径规则一致)
user_vector_path = os.path.join("./vector_stores", str(user_id))

# 只有当内存中没有，且硬盘上有时，才加载
if "vector_store" not in st.session_state or st.session_state.vector_store is None:
    if os.path.exists(user_vector_path):
        try:
            # 必须重新定义 Embeddings，且要和 utils.py 里的一模一样
            embeddings = DashScopeEmbeddings(model="text-embedding-v1")
            # 从硬盘读取
            st.session_state.vector_store = FAISS.load_local(
                user_vector_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print(f"🔄 刷新页面：已从硬盘恢复用户 {user_id} 的向量库")
        except Exception as e:
            print(f"警告：无法加载用户 {user_id} 的历史向量库: {e}")
            st.session_state.vector_store = None
    else:
        # 如果硬盘上没有，初始化为空
        st.session_state.vector_store = None

# --- 2.2 初始化聊天历史 (保持不变，但位置调整) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# 2. ✅ 优化点：在页面加载时就立即初始化 LLM 模型
if "llm" not in st.session_state:
    try:
        st.session_state.llm = get_llm()
        if not st.session_state.llm:
            raise ValueError("模型初始化返回为空")
        print("✅ 模型在页面初始化阶段已加载")
    except Exception as e:
        st.error("AI 模型加载失败，请检查 API Key 配置")
        st.stop() # 直接停止，不需要继续渲染界面
 
# --- 2. 页面配置 ---
st.set_page_config(page_title="法律 AI 助手", page_icon="⚖️")
# st.title("⚖ 合同问答助手")


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
                vector_store, processed_files = process_uploaded_files(uploaded_files, user_id)
                
                if vector_store:
                    st.session_state.vector_store = vector_store
                     # ✅ 必须同时更新内存，否则当前轮次的 AI 问答逻辑读不到新数据
                     # ✅ utils.py 已经通过 save_local 存到了硬盘
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
 
user_question = st.chat_input("请输入...",key="chat_input")

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
                    llm = st.session_state.llm 
                                
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
**对话历史：**
{chat_history}
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
                        
                        # 替换你原来的 format_chat_history 函数
                        def format_chat_history(history):
                            if not history:
                                return "无历史对话"
    
                            # ✅ 优化：直接按角色拼接，结构更清晰
                            lines = []
                            # 只取最近的 5 轮（防止 token 超限）
                            for q, a in history[-5:]:
                                lines.append(f"用户: {q}")
                                lines.append(f"AI: {a}")
    
                            return "\n".join(lines)
                        formatted_history = format_chat_history(st.session_state.chat_history)
                         
                        # 6. 调用链
                        response = rag_chain.invoke({
                            "context": context_text, 
                            "question": user_question,
                            "chat_history": formatted_history
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
                     
                    final_response = response
                    st.markdown(final_response)
                # **********************************************************
                # ✅ 关键结合点：保存对话到 MySQL (带 user_id)
                # **********************************************************
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            # 先存用户的问题
                            cursor.execute(
                            "INSERT INTO chat_logs (user_id, role, content) VALUES (%s, 'user', %s)",
                            (user_id, user_question)
                            )
                            # 再存 AI 的回答
                            cursor.execute(
                            "INSERT INTO chat_logs (user_id, role, content) VALUES (%s, 'assistant', %s)",
                            (user_id, final_response)
                            )   
                            conn.commit()
                            # st.success("已保存到历史记录", icon="💾") # 可选：给个提示
                        except Exception as e:
                            print(f"保存失败: {e}")
                            # st.warning("对话已结束，但未保存到历史记录")
                        finally:
                            conn.close() # 确保数据库连接关闭
    
                     # 6. 更新 Session State (内存同步)
                    st.session_state.chat_history.append((user_question, final_response))
                # ✅ 新增：捕获模型调用错误
                except Exception as e:
                    error_msg = f"❌ AI 处理出错: {str(e)}"
                    st.error(error_msg)
                    print(f"AI 调用错误: {e}") # 打印到控制台
# st.write("Debug - Vector Store State:", st.session_state.vector_store is not None)