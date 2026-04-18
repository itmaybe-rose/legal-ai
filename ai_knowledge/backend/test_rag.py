"""
测试RAG增强的知识图谱生成功能
"""
import time
from vector_db import get_vector_db

# 测试向量数据库
print("测试向量数据库...")
db = get_vector_db()

# 添加测试数据
test_jobs = [
    {"title": "Java工程师", "company": "字节跳动", "salary": "20K-40K", "location": "北京", "experience": "3-5年", "education": "本科", "skills": ["Java", "Spring", "MySQL"]},
    {"title": "Python工程师", "company": "阿里巴巴", "salary": "25K-45K", "location": "杭州", "experience": "1-3年", "education": "本科", "skills": ["Python", "Django", "Flask"]},
    {"title": "前端工程师", "company": "腾讯", "salary": "18K-35K", "location": "深圳", "experience": "2-4年", "education": "本科", "skills": ["Vue", "React", "TypeScript"]}
]

test_exams = [
    {"school": "清华大学", "major": "计算机科学", "direction": "人工智能", "exam_courses": ["政治", "英语", "数学", "计算机专业基础"], "score_line": "350分", "enrollment": "30人"},
    {"school": "北京大学", "major": "计算机科学", "direction": "软件工程", "exam_courses": ["政治", "英语", "数学", "数据结构"], "score_line": "340分", "enrollment": "25人"}
]

# 添加数据到向量数据库
db.add_jobs(test_jobs)
db.add_exams(test_exams)

print(f"向量数据库数据量: {db.get_size()}")

# 测试搜索
print("\n测试搜索功能...")
query = "计算机科学 就业"
start_time = time.time()
results = db.search(query, top_k=3)
end_time = time.time()

print(f"搜索耗时: {end_time - start_time:.4f} 秒")
print("搜索结果:")
for i, result in enumerate(results, 1):
    print(f"{i}. {result}")

# 测试知识图谱生成
print("\n测试知识图谱生成...")
from main import generate_plan_with_llm

start_time = time.time()
result = generate_plan_with_llm("计算机科学", "就业")
end_time = time.time()

print(f"知识图谱生成耗时: {end_time - start_time:.2f} 秒")
print("生成结果:")
print(f"概要: {result.summary}")
print(f"技能树节点数: {len(result.skill_tree)}")
print(f"推荐资源数: {len(result.resources)}")
print(f"就业岗位数: {len(result.job_market)}")
