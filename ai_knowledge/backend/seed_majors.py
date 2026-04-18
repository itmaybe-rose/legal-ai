import requests
import pymysql
import re
from bs4 import BeautifulSoup

# --- 配置数据库连接 (使用与应用相同的配置) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'campus_ai',
    'charset': 'utf8mb4'
}

def fetch_and_save_majors():
    # 1. 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("正在获取专业数据...")
    
    # 2. 使用阳光高考网的本科专业目录
    # 这是一个更可靠的数据源
    base_url = "https://gaokao.chsi.com.cn/zyk/pub/zyml/"
    
    try:
        # 添加请求头模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找专业列表
            major_list = []
            
            # 查找所有专业类别
            category_divs = soup.find_all('div', class_='zy-list')
            
            for category_div in category_divs:
                # 查找类别下的专业
                major_items = category_div.find_all('a')
                for item in major_items:
                    major_name = item.text.strip()
                    if major_name and len(major_name) > 0:
                        major_list.append(major_name)
            
            print(f"共找到 {len(major_list)} 个专业")
            
            # 3. 保存到数据库
            count = 0
            for major_name in major_list:
                try:
                    cursor.execute("INSERT IGNORE INTO majors (name, college) VALUES (%s, %s)", (major_name, "综合"))
                    count += 1
                except Exception as e:
                    pass # 忽略重复插入的错误
            
            print(f"成功插入 {count} 个专业")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生错误: {e}")

    # 4. 提交并关闭
    conn.commit()
    cursor.close()
    conn.close()
    print("数据入库完成！请去数据库查看。")

if __name__ == "__main__":
    fetch_and_save_majors()