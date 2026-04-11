import streamlit as st
import mysql.connector
from mysql.connector import Error
import bcrypt
import os

from dotenv import load_dotenv

# 1. 加载环境变量
load_dotenv()

# 2. 页面配置
st.set_page_config(page_title="Legal AI - 登录", page_icon="⚖️")

# --- 新增：导入 Cookie 管理器 ---
from streamlit_cookies_manager import EncryptedCookieManager
cookies = EncryptedCookieManager(
    prefix="legal-ai-assistant",
    password="your-super-secret-password" # 请保持这个密码不变
)
if not cookies.ready():
    st.stop()
# 3. 数据库连接函数 (优化：增加连接超时设置，防止卡死)
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "legal_ai_assistant"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            connection_timeout=10  # 10秒超时，防止数据库未启动时卡住
        )
    except Error as e:
        # 仅在调试模式下打印详细错误，避免暴露给用户
        print(f"数据库连接错误: {e}")
        return None

# 4. 验证密码
def verify_password(stored_hash, provided_password):
    try:
        # 确保 stored_hash 是 bytes 格式
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False

# 5. 注册逻辑 (侧边栏)
def register():
    with st.sidebar.expander("没有账号？点击注册"):
        with st.form("reg_form"):
            reg_user = st.text_input("新用户名", key="reg_user")
            reg_pass = st.text_input("新密码", type="password", key="reg_pass")
            reg_submit = st.form_submit_button("立即注册")
            
            if reg_submit:
                if not reg_user or not reg_pass:
                    st.warning("请填写完整信息")
                elif len(reg_pass) < 6:
                    st.warning("密码长度不能少于6位")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        # 使用 bcrypt 加密密码
                        salt = bcrypt.gensalt()
                        hashed = bcrypt.hashpw(reg_pass.encode('utf-8'), salt)
                        
                        try:
                            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                                           (reg_user, hashed))
                            conn.commit()
                            st.success("✅ 注册成功！请登录。")
                            # 注册成功后，清空输入框
                            st.rerun() 
                        except Error as e:
                            if "Duplicate entry" in str(e):
                                st.error("❌ 用户名已存在，请换一个。")
                            else:
                                st.error("❌ 注册失败，请稍后重试。")
                                print(f"数据库错误: {e}")
                        finally:
                            conn.close()

# 6. 登录逻辑
def login():
    st.title("⚖️ 法律 AI 助手")
    # st.markdown("### 请登录以继续使用")
    
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        submit = st.form_submit_button("登 录", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.warning("请输入用户名和密码")
            else:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    # 查询用户
                    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    # 验证密码
                    if result and verify_password(result[0], password):
                        st.success("登录成功！正在跳转...")
                        # 记录登录状态
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        # 2. 设置 Cookies (硬盘中，持久化)
                        cookies["logged_in"] = "true" # 必须是字符串
                        cookies["username"] = username
                        cookies.save() # 必须调用 save 才会写入浏览器
                        # 强制刷新页面，触发下方的跳转逻辑
                        st.rerun()
                    else:
                        st.error("❌ 用户名或密码错误")

# 7. 主程序流程控制
def main():
    # --- 核心修改：检查 Cookies 并自动恢复 Session State ---
    # 如果 Session 中未登录，但 Cookies 里有记录，则自动登录
    if not st.session_state.get("logged_in"):
        if cookies.get("logged_in") == "true":
            st.session_state["logged_in"] = True
            st.session_state["username"] = cookies.get("username")
    # 优先检查登录状态
    if st.session_state.get("logged_in"):
        # 如果已登录，直接跳转到核心应用页面
        st.switch_page("pages/app.py")
    
    # 如果未登录，显示登录页和注册栏
    login()
    register()

if __name__ == "__main__":
    main()