"""
测试知识图谱预生成与缓存系统
"""
import json
from knowledge_base import get_course_db
from scheduler import TaskScheduler

# 测试数据库连接和表结构
print("测试数据库连接和表结构...")
db = get_course_db()
print("数据库连接成功")

# 测试模板保存和读取
print("\n测试模板保存和读取...")
test_template = {
    "summary": "测试模板",
    "skill_tree": [
        {
            "id": "1",
            "label": "核心技能",
            "level": "core",
            "mastered": False,
            "children": []
        }
    ],
    "resources": [
        {
            "title": "推荐课程",
            "difficulty": "青铜",
            "source": "在线平台",
            "desc": "基础课程",
            "job_relevance": "通用"
        }
    ],
    "job_market": []
}

# 保存测试模板
db.save_plan_template("计算机科学", "就业", test_template)
print("保存测试模板成功")

# 读取测试模板
loaded_template = db.get_plan_template("计算机科学", "就业")
print(f"加载模板成功: {json.dumps(loaded_template, ensure_ascii=False)[:100]}...")

# 测试缓存机制
print("\n测试缓存机制...")
# 再次读取，应该从缓存获取
loaded_template2 = db.get_plan_template("计算机科学", "就业")
print("第二次加载成功（应该从缓存获取）")

# 测试生成知识图谱
print("\n测试生成知识图谱...")
TaskScheduler._generate_knowledge_graphs()
print("知识图谱生成测试完成")

# 测试读取生成的知识图谱
print("\n测试读取生成的知识图谱...")
cs_job_plan = db.get_plan_template("计算机科学", "就业")
print(f"计算机科学-就业: {cs_job_plan['summary']}")

ai_study_plan = db.get_plan_template("人工智能", "考研")
print(f"人工智能-考研: {ai_study_plan['summary']}")

print("\n所有测试完成！")