# pages/app.py - 法律AI助手主页面

import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from config import COOKIE_PREFIX, COOKIE_PASSWORD
from database import get_user_id, save_chat_message, load_chat_history, delete_chat_history, export_chat_history
from document_processor import process_uploaded_files, get_existing_file_names, remove_files_from_vector_store, clear_all_files, load_vector_store
from chat_manager import get_llm, process_user_question

st.set_page_config(page_title="法律 AI 助手", page_icon="⚖️")

cookies = EncryptedCookieManager(
    prefix=COOKIE_PREFIX,
    password=COOKIE_PASSWORD
)
if not cookies.ready():
    st.stop()

if "logged_in" not in st.session_state:
    if cookies.get("logged_in") == "true":
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookies.get("username")

if not st.session_state.get("logged_in"):
    st.switch_page("main.py")

current_username = st.session_state["username"]
user_id = get_user_id(current_username)
if not user_id:
    st.error("用户身份验证失败，请重新登录")
    st.stop()

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history(user_id)

api_key = os.getenv("DASHSCOPE_API_KEY")

if "llm" not in st.session_state:
    try:
        st.session_state.llm = get_llm()
        if not st.session_state.llm:
            raise ValueError("模型初始化返回为空")
    except Exception as e:
        st.error("AI 模型加载失败，请检查 API Key 配置")
        st.stop()

if not st.session_state.vector_store:
    st.info("👋 你好！我是法律助手。")
    st.write("请在侧边栏上传您的合同或法律文件，我可以帮您分析条款。")
else:
    st.success("📄 文件已加载！您可以开始提问关于该文档的法律问题。")

if "user_question" in st.session_state:
    st.session_state.user_question = ""

with st.sidebar:
    st.write(f"欢迎, {st.session_state.username}")

    if st.button("退出登录", use_container_width=True):
        if "vector_store" in st.session_state:
            del st.session_state.vector_store
        if "chat_history" in st.session_state:
            del st.session_state.chat_history
        st.session_state.logged_in = False
        st.session_state.username = None
        cookies["logged_in"] = ""
        cookies["username"] = ""
        cookies.save()
        st.success("已退出")
        st.rerun()

    # 聊天历史搜索
    st.markdown("---")
    st.subheader("🔍 搜索对话")
    search_query = st.text_input("输入关键词搜索", key="search_input")
    
    # 搜索结果展示（语义相似度匹配）
    if search_query.strip() and st.session_state.chat_history:
        matched_results = []
        query_words = set(search_query.lower().split())
        
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            # 提取问题和回答中的所有单词
            text = (question + " " + answer).lower()
            text_words = set(text.split())
            
            # 计算语义相似度：Jaccard相似度
            intersection = query_words & text_words
            union = query_words | text_words
            
            if union:
                similarity = len(intersection) / len(union)
            else:
                similarity = 0
            
            # 同时检查精确匹配（提高召回率）
            exact_match = any(word in text for word in query_words)
            
            # 设置匹配阈值
            if similarity >= 0.2 or exact_match:
                # 综合评分：语义相似度 + 精确匹配加分
                match_score = similarity + (1 if exact_match else 0)
                
                # 预览匹配内容（显示匹配的部分）
                preview = question[:60] + "..." if len(question) > 60 else question
                matched_results.append((i, match_score, preview))
        
        # 按匹配度排序
        matched_results.sort(key=lambda x: x[1], reverse=True)
        
        if matched_results:
            st.success(f"找到 {len(matched_results)} 条匹配")
            for idx, score, preview in matched_results:
                # 将滚动逻辑内联到按钮中，通过window.parent访问主页面
                import streamlit.components.v1 as components
                button_html = f"""
                <style>
                    .search-result-btn {{
                        width: 100%;
                        padding: 12px;
                        margin: 6px 0;
                        background: #374151;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        text-align: left;
                        font-size: 14px;
                        white-space: normal;
                        line-height: 1.5;
                        min-height: 60px;
                        max-height: 120px;
                        overflow-y: auto;
                        transition: background 0.2s;
                    }}
                    .search-result-btn:hover {{
                        background: #4B5563;
                    }}
                </style>
                <button class="search-result-btn" onclick="(function() {{
                    var element = window.parent.document.getElementById('chat-{idx}');
                    if (element) {{
                        element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        element.style.border = '3px solid #4CAF50';
                        element.style.backgroundColor = '#e8f5e9';
                        element.style.boxShadow = '0 0 25px rgba(76, 175, 80, 0.5)';
                    }}
                }})()">
                    📝 {preview}
                </button>
                """
                components.html(button_html, height=140, width=280)

    # 聊天历史管理
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("📋 对话管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清空历史", use_container_width=True):
                if delete_chat_history(user_id):
                    st.session_state.chat_history = []
                    st.success("已清空")
                    st.rerun()
                else:
                    st.error("清空失败")
        
        with col2:
            export_format = st.selectbox("导出", ["JSON", "TXT"], label_visibility="collapsed")
            if st.button("📥 导出", use_container_width=True):
                format = 'json' if export_format == "JSON" else 'txt'
                success, content, filename = export_chat_history(user_id, format)
                if success:
                    st.download_button(
                        label=f"下载 {filename}",
                        data=content,
                        file_name=filename,
                        mime="application/json" if format == 'json' else "text/plain",
                        use_container_width=True
                    )
                else:
                    st.error("导出失败")

    st.markdown("---")
    st.subheader("📁 文件上传")
    uploaded_files = st.file_uploader(
        "上传文件",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    # 文件管理
    st.markdown("---")
    st.subheader("📋 已上传文件")
    
    if st.session_state.vector_store:
        existing_files = get_existing_file_names(st.session_state.vector_store)
        
        if existing_files:
            selected_files = st.multiselect(
                "选择要删除的文件",
                existing_files,
                default=[]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ 删除选中", use_container_width=True, disabled=len(selected_files) == 0):
                    st.session_state.vector_store, removed_count = remove_files_from_vector_store(
                        st.session_state.vector_store,
                        selected_files,
                        user_id
                    )
                    if removed_count > 0:
                        st.success(f"已删除 {', '.join(selected_files)}")
                        remaining_files = get_existing_file_names(st.session_state.vector_store)
                        if not remaining_files:
                            st.session_state.vector_store = None
                            st.session_state.chat_history = []
                    st.rerun()
            
            with col2:
                if st.button("🧹 清空全部", use_container_width=True):
                    if clear_all_files(user_id):
                        st.session_state.vector_store = None
                        st.session_state.chat_history = []
                        st.success("已清空所有文件")
                    else:
                        st.error("清空失败")
                    st.rerun()
        else:
            st.info("暂无文件")
    else:
        st.info("暂无文件，请先上传")

if uploaded_files is not None and len(uploaded_files) > 0:
    current_file_names = [f.name for f in uploaded_files]

    if ('last_uploaded_files' not in st.session_state or
        st.session_state.last_uploaded_files != current_file_names):

        st.session_state.last_uploaded_files = current_file_names

        progress_bar = st.progress(0, text="准备处理...")
        status_text = st.empty()

        def update_progress(message, progress):
            status_text.text(message)
            progress_bar.progress(min(progress / 100.0, 0.99), text=message)

        st.session_state.vector_store = None

        vector_store, processed_files, error_messages = process_uploaded_files(
            uploaded_files, 
            user_id,
            progress_callback=update_progress
        )

        progress_bar.progress(100, text="完成")

        if vector_store:
            st.session_state.chat_history = []
            st.session_state.vector_store = vector_store
            st.session_state.processed_files = processed_files
            st.success(f"✅ 已加载新文件: {', '.join(processed_files)}")
            if error_messages:
                st.warning("⚠️ 部分文件处理异常:\n" + "\n".join(error_messages))
        else:
            st.error("文件处理失败")
            if error_messages:
                st.error("详细错误: " + error_messages[0])

        progress_bar.empty()
        status_text.empty()

st.subheader("聊天历史")

# 获取侧边栏的搜索关键词
search_query = st.session_state.get("search_input", "")

# 检查URL参数获取要滚动到的对话索引
scroll_to_idx = -1
try:
    scroll_param = st.query_params.get("scroll_to", "-1")
    scroll_to_idx = int(scroll_param)
except:
    scroll_to_idx = -1

# 清除URL参数（只执行一次滚动）
if "scroll_to" in st.query_params:
    del st.query_params["scroll_to"]

# 预计算所有匹配的对话（使用语义相似度）
matched_indices = set()
if search_query.strip() and st.session_state.chat_history:
    query_words = set(search_query.lower().split())
    
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        text = (question + " " + answer).lower()
        text_words = set(text.split())
        
        # Jaccard相似度
        intersection = query_words & text_words
        union = query_words | text_words
        similarity = len(intersection) / len(union) if union else 0
        
        # 精确匹配检查
        exact_match = any(word in text for word in query_words)
        
        if similarity >= 0.15 or exact_match:
            matched_indices.add(i)

# 聊天历史显示
if not st.session_state.chat_history:
    st.info("暂无历史记录，请在下方提问。")
else:
    # 显示搜索提示
    if search_query.strip():
        if matched_indices:
            st.info(f"🔍 搜索结果：高亮显示 {len(matched_indices)} 条匹配对话")
        else:
            st.info("🔍 未找到匹配的对话，显示全部历史")
    
    # 显示所有对话历史
    for i, (question, answer) in enumerate(st.session_state.chat_history):
        # 检查是否需要高亮显示（搜索匹配或跳转目标）
        is_highlighted = i in matched_indices
        is_jump_target = i == scroll_to_idx
        
        with st.chat_message("user"):
            # 添加锚点和高亮样式
            if is_jump_target:
                # 跳转目标 - 绿色高亮
                st.markdown(f'<div id="chat-{i}" style="background-color: #e8f5e9; padding: 12px; border-radius: 6px; border: 3px solid #4CAF50; box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);">', unsafe_allow_html=True)
            elif is_highlighted:
                # 搜索匹配 - 黄色高亮
                st.markdown(f'<div id="chat-{i}" style="background-color: #fff3cd; padding: 12px; border-radius: 6px; border-left: 4px solid #FFC107;">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div id="chat-{i}">', unsafe_allow_html=True)
            
            st.write(question)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.chat_message("assistant"):
            # 高亮匹配内容
            highlighted_answer = answer
            if is_highlighted and search_query.strip():
                # 高亮所有匹配的词
                for word in search_query.split():
                    highlighted_answer = highlighted_answer.replace(
                        word, 
                        f'<mark style="background-color: yellow; padding: 1px 3px; border-radius: 2px;">{word}</mark>'
                    )
            st.markdown(highlighted_answer, unsafe_allow_html=True)
    
    # 自动滚动到目标对话（使用URL参数方式）
    if scroll_to_idx >= 0 and scroll_to_idx < len(st.session_state.chat_history):
        import streamlit.components.v1 as components
        scroll_script = f"""
        <script>
            // 参考专业AI应用的滚动实现
            (function() {{
                function scrollToChat() {{
                    var element = document.getElementById('chat-{scroll_to_idx}');
                    if (element) {{
                        // 使用原生滚动API
                        element.scrollIntoView({{ 
                            behavior: 'smooth', 
                            block: 'center', 
                            inline: 'nearest' 
                        }});
                        // 添加动态高亮效果
                        element.style.border = '3px solid #4CAF50';
                        element.style.backgroundColor = '#e8f5e9';
                        element.style.boxShadow = '0 0 25px rgba(76, 175, 80, 0.5)';
                        element.style.transition = 'all 0.5s ease';
                        // 添加脉冲动画
                        element.animate([
                            {{ boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.4)' }},
                            {{ boxShadow: '0 0 0 15px rgba(76, 175, 80, 0)' }}
                        ], {{
                            duration: 1000,
                            iterations: 2
                        }});
                        return true;
                    }}
                    return false;
                }}
                
                // 多重保障机制
                var attempts = 0;
                var maxAttempts = 20;
                
                function tryScroll() {{
                    attempts++;
                    if (scrollToChat()) {{
                        return;
                    }} else if (attempts < maxAttempts) {{
                        setTimeout(tryScroll, 100);
                    }}
                }}
                
                // 立即执行
                tryScroll();
                
                // 监听页面完全加载
                window.addEventListener('load', function() {{
                    scrollToChat();
                }});
                
                // 请求动画帧
                requestAnimationFrame(function() {{
                    scrollToChat();
                }});
                
                // 延迟执行
                setTimeout(function() {{
                    scrollToChat();
                }}, 500);
            }})();
        </script>
        """
        components.html(scroll_script, height=0, width=0)

st.divider()

# 添加全局滚动函数（放在页面底部确保所有元素都已加载）
import streamlit.components.v1 as components
components.html("""
<script>
    // 全局滚动函数，供侧边栏按钮调用
    window.scrollToChat = function(idx) {
        var element = document.getElementById('chat-' + idx);
        if (element) {
            // 平滑滚动到目标元素，居中显示
            element.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center', 
                inline: 'nearest' 
            });
            
            // 添加高亮样式
            element.style.border = '3px solid #4CAF50';
            element.style.backgroundColor = '#e8f5e9';
            element.style.boxShadow = '0 0 25px rgba(76, 175, 80, 0.5)';
            element.style.transition = 'all 0.5s ease';
            
            // 添加脉冲动画
            element.animate([
                { boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.4)' },
                { boxShadow: '0 0 0 20px rgba(76, 175, 80, 0)' }
            ], {
                duration: 1000,
                iterations: 2
            });
        } else {
            console.log('Element chat-' + idx + ' not found');
        }
    }
</script>
""", height=0, width=0)

user_question = st.chat_input("请输入...", key="chat_input")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)

    with st.chat_message("assistant"):
        try:
            final_response, retrieved_docs = process_user_question( 
                user_question,
                st.session_state.vector_store,
                st.session_state.chat_history,
                st.session_state.llm,
                api_key
            ) 

            if final_response is None:
                st.warning(retrieved_docs)
            else:
                try:
                    save_chat_message(user_id, "user", user_question)
                    save_chat_message(user_id, "assistant", final_response)
                except Exception as e:
                    print(f"保存失败: {e}")

                st.session_state.chat_history.append((user_question, final_response))
                st.rerun()

        except Exception as e:
            st.error(f"❌ AI 处理出错: {str(e)}")
            print(f"AI 调用错误: {e}")