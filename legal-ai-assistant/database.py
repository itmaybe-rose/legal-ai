# database.py - 数据库操作模块

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

def get_user_id(username):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    return None

def save_chat_message(user_id, role, content):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (user_id, role, content) VALUES (%s, %s, %s)",
            (user_id, role, content)
        )
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"保存聊天记录失败: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def load_chat_history(user_id, limit=50):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM chat_logs WHERE user_id = %s ORDER BY timestamp ASC LIMIT %s",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        temp_hist = []
        for row in rows:
            temp_hist.append((row[1], "") if row[0] == "user" else ("", row[1]))
        chat_history = []
        for i in range(0, len(temp_hist) - 1, 2):
            if i + 1 < len(temp_hist):
                chat_history.append((temp_hist[i][0], temp_hist[i + 1][1]))
        return chat_history
    except Exception as e:
        print(f"加载聊天历史失败: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def delete_chat_history(user_id):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_logs WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"删除聊天历史失败: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def export_chat_history(user_id, format='json'):
    """
    导出聊天历史
    
    Args:
        user_id: 用户ID
        format: 导出格式，支持 'json' 或 'txt'
        
    Returns:
        (success, content, filename)
    """
    conn = get_db_connection()
    if not conn:
        return False, "", ""
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, role, content FROM chat_logs WHERE user_id = %s ORDER BY timestamp ASC",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        if format == 'json':
            import json
            history = []
            for row in rows:
                history.append({
                    'timestamp': row[0].isoformat() if row[0] else '',
                    'role': row[1],
                    'content': row[2]
                })
            content = json.dumps(history, ensure_ascii=False, indent=2)
            filename = f"chat_history_{user_id}.json"
        else:
            content = ""
            for row in rows:
                timestamp = row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else ''
                content += f"[{timestamp}] {row[1]}: {row[2]}\n\n"
            filename = f"chat_history_{user_id}.txt"
        
        return True, content, filename
    
    except Exception as e:
        print(f"导出聊天历史失败: {e}")
        return False, "", ""
    finally:
        if conn and conn.is_connected():
            conn.close()