from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import User, Major, City, Spot, Route, RouteStep, Post, Comment, Like, UserSettings
# from passlib.context import CryptContext
from passlib.hash import sha256_crypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from functools import lru_cache

from fastapi import UploadFile, File
import os
import uuid
import shutil 

# 定义上传目录
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 1. 导入 LangChain 相关库
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from dotenv import load_dotenv
load_dotenv() 

# 在文件顶部定义全局缓存
PLAN_CACHE = {} 

def get_cached_plan(major, goal):
    return PLAN_CACHE.get(f"{major}_{goal}")

def cache_plan(major, goal, plan):
    PLAN_CACHE[f"{major}_{goal}"] = plan

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI() #创建FastAPI实例



from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")


# 2. 初始化 LangChain 的模型

llm = ChatOpenAI(
  model="qwen-max", 
  api_key=os.getenv("DASHSCOPE_API_KEY"),
  base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
  temperature=0.3,  # 降低温度，减少随机性，提高生成速度
  max_tokens=800,   # 限制生成长度，加快生成速度
  top_p=0.8          # 调整top_p，加快生成速度
)

# --- RAG 系统组件 ---
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.embeddings import Embeddings

# 简单的文本分割器实现
class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text):
        # 简单实现：按固定长度分割文本
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

# 简单的嵌入模型实现
class SimpleEmbeddings(Embeddings):
    def embed_documents(self, texts):
        # 简单实现，实际应用中应该使用真实的嵌入模型
        return [[0.1 for _ in range(10)] for _ in texts]
    
    def embed_query(self, text):
        return [0.1 for _ in range(10)]

# 课程知识库
class CourseKnowledgeBase:
    def __init__(self):
        self.embeddings = SimpleEmbeddings()
        self.vector_store = InMemoryVectorStore(embedding=self.embeddings)
        self.text_splitter = SimpleTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    def add_course(self, course_text):
        # 分割文本并添加到向量存储
        chunks = self.text_splitter.split_text(course_text)
        self.vector_store.add_texts(chunks)
    
    def retrieve_courses(self, query, k=3):
        # 根据查询检索相关课程
        return self.vector_store.similarity_search(query, k=k)

# 初始化课程知识库
course_knowledge_base = CourseKnowledgeBase()

# --- 微调功能组件 ---

# 课程领域提示词模板库
course_templates = {
    "computer_science": {
        "job": "你是一位计算机科学领域的专家，专注于就业方向。请根据用户的专业背景和目标岗位，生成一份详细的学习路径，包括核心技能、推荐课程和就业建议。",
        "study": "你是一位计算机科学领域的教育专家，专注于考研方向。请根据用户的专业背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位计算机科学领域的创业导师，专注于创业方向。请根据用户的专业背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "ai": {
        "job": "你是一位人工智能领域的专家，专注于就业方向。请根据用户的专业背景和目标岗位，生成一份详细的学习路径，包括核心技能、推荐课程和就业建议。",
        "study": "你是一位人工智能领域的教育专家，专注于考研方向。请根据用户的专业背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位人工智能领域的创业导师，专注于创业方向。请根据用户的专业背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "data_science": {
        "job": "你是一位数据科学领域的专家，专注于就业方向。请根据用户的专业背景和目标岗位，生成一份详细的学习路径，包括核心技能、推荐课程和就业建议。",
        "study": "你是一位数据科学领域的教育专家，专注于考研方向。请根据用户的专业背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位数据科学领域的创业导师，专注于创业方向。请根据用户的专业背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "finance": {
        "job": "你是一位金融领域的专家，专注于就业方向。请根据用户的金融背景和目标岗位，生成一份详细的学习路径，包括核心金融知识、推荐课程和就业建议。",
        "study": "你是一位金融领域的教育专家，专注于考研方向。请根据用户的金融背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位金融领域的创业导师，专注于创业方向。请根据用户的金融背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "economics": {
        "job": "你是一位经济学领域的专家，专注于就业方向。请根据用户的经济学背景和目标岗位，生成一份详细的学习路径，包括核心经济知识、推荐课程和就业建议。",
        "study": "你是一位经济学领域的教育专家，专注于考研方向。请根据用户的经济学背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位经济学领域的创业导师，专注于创业方向。请根据用户的经济学背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "management": {
        "job": "你是一位管理学领域的专家，专注于就业方向。请根据用户的管理背景和目标岗位，生成一份详细的学习路径，包括核心管理知识、推荐课程和就业建议。",
        "study": "你是一位管理学领域的教育专家，专注于考研方向。请根据用户的管理背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位管理学领域的创业导师，专注于创业方向。请根据用户的管理背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "accounting": {
        "job": "你是一位会计学领域的专家，专注于就业方向。请根据用户的会计背景和目标岗位，生成一份详细的学习路径，包括核心会计知识、推荐课程和就业建议。",
        "study": "你是一位会计学领域的教育专家，专注于考研方向。请根据用户的会计背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位会计学领域的创业导师，专注于创业方向。请根据用户的会计背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    },
    "general": {
        "job": "你是一位教育专家，专注于就业方向。请根据用户的专业背景和目标岗位，生成一份详细的学习路径，包括核心技能、推荐课程和就业建议。",
        "study": "你是一位教育专家，专注于考研方向。请根据用户的专业背景和考研目标，生成一份详细的学习路径，包括核心课程、复习计划和考试建议。",
        "startup": "你是一位创业导师，专注于创业方向。请根据用户的专业背景和创业目标，生成一份详细的学习路径，包括必备技能、项目经验和创业建议。"
    }
}

# 课程领域术语库
course_terms = {
    "computer_science": ["数据结构", "算法", "操作系统", "计算机网络", "数据库", "软件工程", "编译原理", "计算机组成原理"],
    "ai": ["机器学习", "深度学习", "神经网络", "自然语言处理", "计算机视觉", "强化学习", "知识图谱", "人工智能伦理"],
    "data_science": ["数据分析", "数据挖掘", "统计学习", "机器学习", "数据可视化", "大数据技术", "数据伦理", "商业智能"],
    "finance": ["金融学", "投资学", "财务管理", "金融市场", "证券投资", "风险管理", "金融工程", "量化分析"],
    "economics": ["微观经济学", "宏观经济学", "计量经济学", "国际经济学", "发展经济学", "行为经济学", "公共经济学", "产业经济学"],
    "management": ["管理学原理", "组织行为学", "市场营销", "人力资源管理", "战略管理", "运营管理", "项目管理", "质量管理"],
    "accounting": ["财务会计", "管理会计", "审计学", "税法", "成本会计", "财务分析", "会计准则", "内部控制"],
    "general": ["专业知识", "技能培养", "实践经验", "职业规划", "行业趋势", "证书考试", "实习经验", "人脉建设"]
}

# 专业分类映射
major_category_map = {
    # 计算机相关
    "计算机科学": "computer_science",
    "计算机科学与技术": "computer_science",
    "软件工程": "computer_science",
    "人工智能": "ai",
    "机器学习": "ai",
    "数据科学": "data_science",
    "大数据": "data_science",
    "网络工程": "computer_science",
    "信息安全": "computer_science",
    
    # 金融相关
    "金融": "finance",
    "金融学": "finance",
    "金融工程": "finance",
    "投资学": "finance",
    "保险学": "finance",
    
    # 经济相关
    "经济学": "economics",
    "国际经济与贸易": "economics",
    "财政学": "economics",
    "税收学": "economics",
    
    # 管理相关
    "工商管理": "management",
    "市场营销": "management",
    "人力资源管理": "management",
    "会计学": "accounting",
    "财务管理": "finance",
    
    # 其他专业
    "数学": "mathematics",
    "物理学": "physics",
    "化学": "chemistry",
    "生物": "biology",
    "医学": "medicine",
    "法学": "law",
    "教育学": "education",
    "文学": "literature",
    "历史": "history",
    "哲学": "philosophy"
}

# 获取专业分类
def get_major_category(major):
    for key, value in major_category_map.items():
        if key in major:
            return value
    # 智能分类：根据关键词判断
    if "计算机" in major or "软件" in major or "编程" in major:
        return "computer_science"
    elif "金融" in major or "投资" in major:
        return "finance"
    elif "经济" in major:
        return "economics"
    elif "管理" in major or "市场" in major:
        return "management"
    elif "会计" in major:
        return "accounting"
    elif "数学" in major:
        return "mathematics"
    elif "物理" in major:
        return "physics"
    elif "化学" in major:
        return "chemistry"
    elif "生物" in major:
        return "biology"
    elif "医学" in major:
        return "medicine"
    elif "法学" in major or "法律" in major:
        return "law"
    elif "教育" in major:
        return "education"
    else:
        return "general"  # 通用分类

# --- 预设知识图谱数据 ---
# 针对标准选项的预设知识图谱，支持快速响应（<50ms）

# 计算机专业-考研预设知识图谱
COMPUTER_SCIENCE_STUDY_PLAN = {
    "summary": "针对计算机科学与技术专业学生的考研学习路径规划",
    "skill_tree": [
        {"id": "1", "label": "数学一", "level": "core", "description": "考研必考科目，包括高数、线代、概率论"},
        {"id": "2", "label": "数据结构与算法", "level": "core", "description": "考研专业课核心，掌握各种数据结构与算法"},
        {"id": "3", "label": "操作系统", "level": "core", "description": "考研专业课，理解进程、内存管理等核心概念"},
        {"id": "4", "label": "计算机网络", "level": "high", "description": "考研专业课，掌握网络协议与体系结构"},
        {"id": "5", "label": "组成原理", "level": "high", "description": "考研专业课，理解计算机硬件系统"},
        {"id": "6", "label": "离散数学", "level": "high", "description": "考研数学基础，集合论、图论等"}
    ],
    "resources": [
        {"type": "book", "title": "《数据结构》严蔚敏", "level": "core"},
        {"type": "book", "title": "《操作系统》汤小丹", "level": "core"},
        {"type": "video", "title": "B站：王道考研数据结构", "level": "core"},
        {"type": "video", "title": "B站：张宇高数基础30讲", "level": "core"},
        {"type": "book", "title": "《计算机网络》谢希仁", "level": "high"}
    ],
    "job_market": []
}

# 计算机专业-就业预设知识图谱
COMPUTER_SCIENCE_JOB_PLAN = {
    "summary": "针对计算机科学与技术专业学生的就业学习路径规划",
    "skill_tree": [
        {"id": "1", "label": "编程语言", "level": "core", "description": "至少精通一门编程语言（Java/Python/C++）"},
        {"id": "2", "label": "数据结构与算法", "level": "core", "description": "面试必备，掌握常见算法与数据结构"},
        {"id": "3", "label": "数据库", "level": "core", "description": "MySQL/Redis/MongoDB等数据库技术"},
        {"id": "4", "label": "Web开发", "level": "high", "description": "前端+后端全栈开发能力"},
        {"id": "5", "label": "Git", "level": "high", "description": "版本控制，团队协作必备"},
        {"id": "6", "label": "Linux", "level": "high", "description": "服务器运维基础能力"}
    ],
    "resources": [
        {"type": "book", "title": "《剑指Offer》", "level": "core"},
        {"type": "video", "title": "B站：LC高频面试题讲解", "level": "core"},
        {"type": "book", "title": "《高性能MySQL》", "level": "high"},
        {"type": "video", "title": "B站：SpringBoot实战", "level": "high"}
    ],
    "job_market": [
        {"name": "Java开发工程师", "salary": "15K-35K", "skills": ["Java", "Spring", "MySQL", "Redis"], "is_core": True},
        {"name": "前端开发工程师", "salary": "12K-30K", "skills": ["Vue", "React", "JavaScript", "CSS"], "is_core": True},
        {"name": "算法工程师", "salary": "25K-50K", "skills": ["Python", "机器学习", "深度学习", "TensorFlow"], "is_core": True},
        {"name": "测试开发工程师", "salary": "12K-25K", "skills": ["Python", "Selenium", "JUnit", "Postman"], "is_core": False},
        {"name": "运维工程师", "salary": "10K-20K", "skills": ["Linux", "Shell", "Docker", "K8s"], "is_core": False}
    ]
}

# 计算机专业-创业预设知识图谱
COMPUTER_SCIENCE_STARTUP_PLAN = {
    "summary": "针对计算机科学与技术专业学生的创业学习路径规划",
    "skill_tree": [
        {"id": "1", "label": "产品设计", "level": "core", "description": "需求分析、原型设计、用户体验"},
        {"id": "2", "label": "全栈开发", "level": "core", "description": "前后端技术都要掌握"},
        {"id": "3", "label": "敏捷开发", "level": "high", "description": "快速迭代开发方法论"},
        {"id": "4", "label": "运营推广", "level": "high", "description": "产品运营、用户增长"},
        {"id": "5", "label": "融资与商业", "level": "high", "description": "商业计划书、路演技巧"}
    ],
    "resources": [
        {"type": "book", "title": "《从0到1》", "level": "core"},
        {"type": "book", "title": "《精益创业》", "level": "core"},
        {"type": "video", "title": "B站：产品经理教程", "level": "high"},
        {"type": "video", "title": "B站：全栈项目实战", "level": "high"}
    ],
    "job_market": []
}

# 计算机专业-考公预设知识图谱
COMPUTER_SCIENCE_CIVIL_PLAN = {
    "summary": "针对计算机科学与技术专业学生的考公学习路径规划",
    "skill_tree": [
        {"id": "1", "label": "行测", "level": "core", "description": "行政职业能力测试，包括言语、判断、资料分析等"},
        {"id": "2", "label": "申论", "level": "core", "description": "写作能力、政策理解与分析"},
        {"id": "3", "label": "数据结构", "level": "high", "description": "部分岗位加试科目"},
        {"id": "4", "label": "政治理论", "level": "high", "description": "时政、马哲、毛中特等"}
    ],
    "resources": [
        {"type": "book", "title": "《行测全真题库》", "level": "core"},
        {"type": "book", "title": "《申论范文100篇》", "level": "core"},
        {"type": "video", "title": "B站：考公上岸经验分享", "level": "core"},
        {"type": "video", "title": "B站：每月时政热点", "level": "high"}
    ],
    "job_market": []
}

# 专业预设方案映射
MAJOR_PLANS = {
    ("计算机科学", "考研"): COMPUTER_SCIENCE_STUDY_PLAN,
    ("计算机科学", "就业"): COMPUTER_SCIENCE_JOB_PLAN,
    ("计算机科学", "创业"): COMPUTER_SCIENCE_STARTUP_PLAN,
    ("计算机科学", "考公"): COMPUTER_SCIENCE_CIVIL_PLAN,
    ("计算机科学与技术", "考研"): COMPUTER_SCIENCE_STUDY_PLAN,
    ("计算机科学与技术", "就业"): COMPUTER_SCIENCE_JOB_PLAN,
    ("计算机科学与技术", "创业"): COMPUTER_SCIENCE_STARTUP_PLAN,
    ("计算机科学与技术", "考公"): COMPUTER_SCIENCE_CIVIL_PLAN,
    ("软件工程", "考研"): COMPUTER_SCIENCE_STUDY_PLAN,
    ("软件工程", "就业"): COMPUTER_SCIENCE_JOB_PLAN,
    ("软件工程", "创业"): COMPUTER_SCIENCE_STARTUP_PLAN,
    ("软件工程", "考公"): COMPUTER_SCIENCE_CIVIL_PLAN,
    ("人工智能", "考研"): {
        **COMPUTER_SCIENCE_STUDY_PLAN,
        "summary": "针对人工智能专业学生的考研学习路径规划",
        "skill_tree": [
            {"id": "1", "label": "数学一", "level": "core", "description": "考研必考科目，高数线代概率论"},
            {"id": "2", "label": "机器学习", "level": "core", "description": "人工智能核心基础"},
            {"id": "3", "label": "深度学习", "level": "core", "description": "神经网络、CNN、RNN等"},
            {"id": "4", "label": "自然语言处理", "level": "high", "description": "NLP核心技术与应用"},
            {"id": "5", "label": "计算机视觉", "level": "high", "description": "图像识别、目标检测等"}
        ]
    },
    ("人工智能", "就业"): {
        **COMPUTER_SCIENCE_JOB_PLAN,
        "summary": "针对人工智能专业学生的就业学习路径规划",
        "job_market": [
            {"name": "算法工程师", "salary": "25K-50K", "skills": ["Python", "TensorFlow", "PyTorch", "深度学习"], "is_core": True},
            {"name": "AI研究员", "salary": "30K-60K", "skills": ["论文复现", "模型优化", "创新研究"], "is_core": True},
            {"name": "数据工程师", "salary": "15K-30K", "skills": ["Python", "Spark", "Hadoop", "数据清洗"], "is_core": True},
            {"name": "产品经理", "salary": "18K-35K", "skills": ["AI产品", "需求分析", "项目管理"], "is_core": False}
        ]
    }
}

# LRU缓存（使用字典实现）
plan_cache = {}
CACHE_MAX_SIZE = 100

def get_cached_plan(major, goal):
    """从缓存获取预设方案"""
    key = (major, goal)
    if key in plan_cache:
        print(f"缓存命中: {key}")
        return plan_cache[key]
    return None

def cache_plan(major, goal, plan):
    """将方案加入缓存"""
    key = (major, goal)
    if len(plan_cache) >= CACHE_MAX_SIZE:
        oldest_key = next(iter(plan_cache))
        del plan_cache[oldest_key]
        print(f"缓存已满，删除最旧项: {oldest_key}")
    plan_cache[key] = plan
    print(f"缓存新方案: {key}")

# 允许跨域（让前端能访问后端）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码处理工具
def get_password_hash(password):
    return sha256_crypt.hash(password)

def verify_password(plain_password, hashed_password):
    return sha256_crypt.verify(plain_password, hashed_password) 

SECRET_KEY = os.getenv("SECRET_KEY")# 从环境变量中获取密钥
ALGORITHM = "HS256"  # ⬅️ 必须加上这一行！
if not SECRET_KEY:
    raise ValueError("SECRET_KEY 环境变量未设置！")


def create_access_token(data: dict):
    to_encode = data.copy()
    # 延长 token 过期时间到 24 小时
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# --- 接口定义 ---

# 1. 注册接口
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # 检查用户是否存在
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    hashed_pw = get_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"msg": "注册成功"}

# 2. 登录接口
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成 Token
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "username": username}

# 定义返回数据的格式（可选，但推荐）
class PlanResponse(BaseModel):
    status: str
    major: str
    plan_text: str
    courses: List[str]

# --- 辅助函数：获取当前登录用户 ---
# 这个函数复用你的 JWT 验证逻辑，确保只有登录用户才能操作
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        print(f"Received token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"Decoded payload: {payload}")
        user_id_str = payload.get("sub")
        print(f"User ID from token (str): {user_id_str}")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
        print(f"User ID from token (int): {user_id}")
    except JWTError as e:
        print(f"JWTError: {e}")
        raise credentials_exception
    except ValueError as e:
        print(f"ValueError: {e}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    print(f"Found user: {user}")
    if user is None:
        raise credentials_exception
    return user

# --- 接口：获取和保存用户资料（含头像上传）---
@app.api_route("/api/profile", methods=["GET", "POST"])
async def handle_profile(
    request: Request, # 引入 Request 对象来判断方法
    name: str = Form(None),
    major: str = Form(None),
    grade: str = Form(None),
    avatar_file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
       # --- 1. 如果是 GET 请求：获取信息 ---
    if request.method == "GET":
        return {
            "name": current_user.name,
            "major": current_user.major,
            "grade": current_user.grade,
            "avatar": current_user.avatar,
            "username": current_user.username,
            "role": current_user.role
        }
    # --- 2. 如果是 POST 请求：保存信息 ---
    # 1. 处理头像上传
   
    if avatar_file and avatar_file.filename:
        # 安全检查：确保是图片
        if not avatar_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="文件必须是图片")
        
        # 保存旧头像路径，用于后续删除
        old_avatar = current_user.avatar
        
        # 生成唯一文件名，防止冲突
        file_ext = os.path.splitext(avatar_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar_file.file, buffer)
            
        # 生成访问 URL (假设你的前端能访问 static 目录)
        current_user.avatar = f"/static/uploads/{unique_filename}"
        
        # 如果用户换了头像，删除旧头像（可选，节省空间）
        if old_avatar and old_avatar != "/static/default-avatar.png":
            old_path = "." + old_avatar # 拼接相对路径
            if os.path.exists(old_path):
                os.remove(old_path)

    # 2. 更新其他信息
    if name: current_user.name = name
    if major: current_user.major = major
    if grade: current_user.grade = grade
    
    db.commit()
    db.refresh(current_user)
    
    return {"msg": "保存成功", "avatar_url": current_user.avatar, "role": current_user.role}


# --- 修改：用户信息接口 (支持修改头像) ---
# 找到 /api/userinfo 接口，将其改为 POST 方法用于更新
@app.post("/api/userinfo")
def update_userinfo(
    name: str = Form(...),
    major: str = Form(...),
    grade: str = Form(...),
    avatar: UploadFile = File(None), # 新增字段
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    # 1. 验证 Token 获取用户 ID (同上文逻辑)
    credentials_exception = HTTPException(status_code=401, detail="无法验证凭证")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 2. 处理头像上传逻辑
    # 如果传了新头像，则保存新文件，并删除旧文件（防止垃圾堆积）
    if avatar and avatar.filename != "":
        if not avatar.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="文件必须是图片")
        
        # 删除旧头像 (注意处理默认头像，不要删了)
        if user.avatar and user.avatar != "/static/default-avatar.png":
            old_path = "." + user.avatar # 拼接相对路径
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # 保存新头像
        ext = os.path.splitext(avatar.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(avatar.file, f)
            
        user.avatar = f"/static/uploads/{filename}"

    # 3. 更新其他信息
    user.name = name
    user.major = major
    user.grade = grade
    
    db.commit()
    db.refresh(user)
    
    return {
        "name": user.name,
        "major": user.major,
        "grade": user.grade,
        "avatar": user.avatar # 返回新路径
    }

# --- 新增：获取专业列表接口 ---
@app.get("/api/options")
def get_options(db: Session = Depends(get_db)):
    # 1. 查询数据库里的所有专业
    majors = db.query(Major).all()
    
    # 2. 提取专业名字，变成 [{"name": "计算机"}, {"name": "软件"}] 这种格式给前端
    # 前端需要这种格式来正确渲染下拉选项
    return {"majors": [{"name": m.name} for m in majors]}
    
    # 或者如果你想把学院也传给前端：
    # return {"majors": [{"name": m.name, "college": m.college} for m in majors]}

# --- 新增：根据专业获取工作岗位列表接口 ---
@app.get("/api/jobs")
def get_jobs(major: str):
    """
    根据专业获取对应的工作岗位列表
    """
    # 使用大模型生成岗位列表
    try:
        print(f"收到专业参数: {major}")
        
        # 直接构建消息
        messages = [
            {
                "role": "user",
                "content": f'请根据专业：{major}，生成该专业常见的工作岗位列表，要求：1. 生成至少10个相关的工作岗位 2. 岗位名称要具体、准确 3. 按照岗位的热门程度排序 4. 每个岗位提供一个简短的描述 5. 直接返回JSON格式，不需要其他文字，JSON结构为：{{"jobs":[{{"id":"岗位ID","name":"岗位名称","description":"岗位描述"}}]}}'
            }
        ]
        
        # 调用大模型
        response = llm.invoke(messages)
        
        print(f"大模型返回内容: {response.content}")
        
        # 解析大模型返回的JSON
        import json
        try:
            # 提取JSON部分
            response_text = response.content
            # 找到JSON开始和结束位置
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            print(f"JSON开始位置: {start_idx}, 结束位置: {end_idx}")
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                print(f"提取的JSON字符串: {json_str}")
                jobs_data = json.loads(json_str)
                
                # 处理岗位ID
                for i, job in enumerate(jobs_data.get('jobs', [])):
                    # 生成唯一ID
                    job_id = job.get('id', job['name'].lower().replace(' ', '_').replace('工程师', '').replace('开发', ''))
                    jobs_data['jobs'][i]['id'] = job_id
                
                print(f"生成的岗位列表: {jobs_data}")
                return jobs_data
        except Exception as e:
            print(f"解析JSON失败: {e}")
            
        # 如果解析失败，返回默认岗位列表
        print("返回默认岗位列表")
        return {"jobs": [
            {"id": "backend", "name": "后端开发工程师", "description": "负责服务器端应用开发，处理数据存储和业务逻辑"},
            {"id": "frontend", "name": "前端开发工程师", "description": "负责用户界面开发，实现网页和移动应用的交互功能"},
            {"id": "fullstack", "name": "全栈开发工程师", "description": "同时负责前端和后端开发，具备完整的应用开发能力"},
            {"id": "ai", "name": "人工智能工程师", "description": "研究和开发AI算法，实现智能系统和应用"},
            {"id": "data", "name": "数据工程师", "description": "负责数据处理、存储和分析，构建数据管道"},
            {"id": "devops", "name": "DevOps工程师", "description": "负责开发和运维的结合，自动化部署和监控"},
            {"id": "test", "name": "测试工程师", "description": "负责软件质量保证，设计和执行测试用例"},
            {"id": "product", "name": "产品经理", "description": "负责产品规划和设计，协调开发和运营"},
            {"id": "ui_ux", "name": "UI/UX设计师", "description": "负责用户界面和用户体验设计"},
            {"id": "project_manager", "name": "项目经理", "description": "负责项目规划、执行和监控，确保项目按时交付"}
        ]}
    except Exception as e:
        print(f"大模型生成失败: {e}")
        # 返回默认岗位列表
        return {"jobs": [
            {"id": "backend", "name": "后端开发工程师", "description": "负责服务器端应用开发，处理数据存储和业务逻辑"},
            {"id": "frontend", "name": "前端开发工程师", "description": "负责用户界面开发，实现网页和移动应用的交互功能"},
            {"id": "fullstack", "name": "全栈开发工程师", "description": "同时负责前端和后端开发，具备完整的应用开发能力"},
            {"id": "ai", "name": "人工智能工程师", "description": "研究和开发AI算法，实现智能系统和应用"},
            {"id": "data", "name": "数据工程师", "description": "负责数据处理、存储和分析，构建数据管道"},
            {"id": "devops", "name": "DevOps工程师", "description": "负责开发和运维的结合，自动化部署和监控"},
            {"id": "test", "name": "测试工程师", "description": "负责软件质量保证，设计和执行测试用例"},
            {"id": "product", "name": "产品经理", "description": "负责产品规划和设计，协调开发和运营"},
            {"id": "ui_ux", "name": "UI/UX设计师", "description": "负责用户界面和用户体验设计"},
            {"id": "project_manager", "name": "项目经理", "description": "负责项目规划、执行和监控，确保项目按时交付"}
        ]}

# --- 1. 定义数据结构 (Pydantic Models) ---
# 这是大模型必须遵守的“输出格式”

class SkillNode(BaseModel):
    id: str = Field(description="唯一ID，例如 '1', '1-1'")
    label: str = Field(description="技能或知识点名称")
    level: str = Field(description="重要程度: core(核心必学/高薪), high(进阶), low(了解)")
    mastered: bool = Field(default=False, description="默认未掌握")
    children: Optional[List['SkillNode']] = Field(default=[], description="子技能节点")

class LearningResource(BaseModel):
    title: str = Field(description="资源标题")
    difficulty: str = Field(description="难度分级: 青铜, 黄金, 王者")
    source: str = Field(description="来源平台，如 Bilibili, GitHub, 官方文档")
    desc: str = Field(description="推荐理由和简介")
    job_relevance: str = Field(description="对应岗位，如 '后端开发工程师'")

class JobMarketData(BaseModel):
    name: str = Field(description="岗位名称")
    salary: str = Field(description="薪资范围")
    skills: List[str] = Field(description="关键技能列表")
    is_core: bool = Field(description="是否核心岗位")

class CareerPlanResponse(BaseModel):
    summary: str = Field(description="针对该目标的简短职业规划建议")
    skill_tree: List[SkillNode] = Field(description="技能树结构")
    resources: List[LearningResource] = Field(description="推荐的学习资源列表")
    job_market: Optional[List[JobMarketData]] = Field(default=[], description="就业风向标数据")

SkillNode.model_rebuild()

# --- 2. 构建 LangChain 逻辑 ---  

from knowledge_base import get_course_db

@lru_cache(maxsize=100)
def generate_plan_with_llm(major: str, goal: str, job: Optional[str] = None) -> CareerPlanResponse:
    # 初始化大模型 (这里以 GPT-4o 为例，因为它对 JSON 支持最好)
    # llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
    
    # 设置输出解析器
    parser = PydanticOutputParser(pydantic_object=CareerPlanResponse)
    
    # 获取专业分类
    major_category = get_major_category(major)
    
    # 获取领域提示词模板
    template_key = "job" if goal == "就业" else "study" if goal == "考研" else "startup"
    domain_template = course_templates.get(major_category, {}).get(template_key, "")
    
    # 获取领域术语
    domain_terms = course_terms.get(major_category, [])
    terms_str = ", ".join(domain_terms)
    
    # 从数据库中检索爬取的专业相关数据
    db = get_course_db()
    
    # 检索相关职位数据（如果是就业目标）
    job_data = []
    if goal == "就业":
        job_data = db.search_jobs(major,limit=3)
    
    # 检索相关考研数据（如果是考研目标）
    exam_data = []
    if goal == "考研":
        exam_data = db.search_exams(major,limit=3)
    
    # 构建爬取数据信息
    scraped_data = ""
    
    if job_data:
        scraped_data += "\n最新职位数据：\n"
        for i, job_item in enumerate(job_data[:3], 1):
            scraped_data += f"{i}. {job_item['title']} - {job_item['company']} (薪资: {job_item['salary']})\n"
            if job_item.get('skills'):
                scraped_data += f"   技能要求: {', '.join(job_item['skills'])}\n"
    
    if exam_data:
        scraped_data += "\n最新考研数据：\n"
        for i, exam_item in enumerate(exam_data[:3], 1):
            scraped_data += f"{i}. {exam_item['school']} - {exam_item['major']}\n"
            if exam_item.get('score_line'):
                scraped_data += f"   分数线: {exam_item['score_line']}\n"
    
    # 使用 RAG 检索相关信息
    from vector_db import get_vector_db
    vector_db = get_vector_db()
    
    # 从向量数据库检索相关信息
    rag_query = f"{major} 专业 {goal} 方向"
    relevant_info = vector_db.search(rag_query, top_k=3)
    
    # 构建RAG检索信息
    rag_info = "\n相关信息：\n"
    for i, info in enumerate(relevant_info, 1):
        rag_info += f"{i}. {info}\n"
    
    # 使用 RAG 检索相关课程
    course_query = f"{major} 专业 {goal} 相关课程"
    relevant_courses = course_knowledge_base.retrieve_courses(course_query)
    
    # 构建课程信息字符串
    courses_info = "\n最新课程推荐：\n"
    for i, course in enumerate(relevant_courses, 1):
        courses_info += f"{i}. {course.page_content}\n"
    
    # 构建领域术语信息
    domain_info = f"\n领域核心术语：\n{terms_str}\n"
    
    # 编写提示词 (Prompt Engineering)
    prompt_template = """
    {domain_template}
    
    用户背景：
    - 专业/领域: {major}
    - 学习目标: {goal}
    - 目标岗位: {job}
    
    领域核心术语：
    {domain_info}
    
    最新课程信息：
    {courses_info}
    
    相关信息：
    {rag_info}
    
    爬取的专业相关数据：
    {scraped_data}
    
    请根据用户的目标、岗位、领域术语、最新课程信息、相关信息和爬取的专业数据，生成一份定制化的学习路径。
    
    要求：
    1. **技能树构建**:
       - 必须与用户的专业领域相关，不要生成与专业无关的技能。
       - 如果是"就业"，侧重实战技能、行业需求和面试高频题。
       - 如果是"考研"，侧重专业基础、考试重点和复习方法。
       - 如果是"创业"，侧重商业思维、市场需求和创新能力。
       - 标记 `level`: "core" 代表核心技能（红色高亮），"high" 代表进阶，"low" 代表了解。
    2. **资源推荐**:
       - 必须包含具体的学习资源，如书籍、视频课程、在线平台等。
       - 结合最新课程信息，推荐与用户专业和目标相关的资源。
       - 按照 "青铜(入门)" -> "黄金(进阶)" -> "王者(实战)" 分级。
    3. **就业风向标**:
       - 如果是"就业"，请基于爬取的职位数据生成至少5个与该专业相关的热门岗位。
       - 每个岗位包含：岗位名称、薪资范围、关键技能列表、是否核心岗位。
       - 按照岗位的热门程度排序。
    4. **格式**: 必须严格遵守 Pydantic 定义的 JSON 格式。
    
    {format_instructions}
    """
    
    prompt = ChatPromptTemplate.from_template(template=prompt_template)
    
    # 构建链
    chain = prompt | llm | parser
    
    # 调用大模型
    try:
        response = chain.invoke({
            "major": major, 
            "goal": goal,
            "job": job if job else "未指定",
            "domain_template": domain_template,
            "domain_info": domain_info,
            "courses_info": courses_info,
            "rag_info": rag_info,
            "scraped_data": scraped_data,
            "format_instructions": parser.get_format_instructions()
        })
        return response
    except Exception as e:
        print(f"LLM Error: {e}")
        # 这里可以加一个降级逻辑，或者抛错
        raise HTTPException(status_code=500, detail="大模型生成失败")

# --- 3. API 接口 ---

@app.post("/api/generate_plan")
async def create_plan(major: str = Form(...), goal: str = Form(...), job: Optional[str] = Form(None)):
    try:
        """
        接收前端传来的专业、方向和目标岗位，返回结构化的图谱数据
        优先使用缓存/数据库预生成方案（<50ms），兜底走大模型生成
        """
        if not major or not goal:
            raise HTTPException(status_code=400, detail="参数缺失")
        
         # 2. 尝试从预设方案映射获取
        # 转换 goal 参数：将前端的英文转换为中文
        goal_map = {
            "job": "就业",
            "study": "考研",
            "exam": "考公",
            "startup": "创业"
        }
        goal_zh = goal_map.get(goal, goal)

        # 4. 尝试从旧的预设方案映射获取
        preset_key = (major, goal_zh)
        if preset_key in MAJOR_PLANS:
            preset_plan = MAJOR_PLANS[preset_key]
            cache_plan(major, goal, preset_plan)
            print(f"使用旧预设方案: {major} - {goal_zh}")
            return preset_plan

        # 1. 优先尝试从缓存获取预设方案
        cached_plan = get_cached_plan(major, goal)
        if cached_plan:
            print(f"使用缓存方案: {major} - {goal}")
            return cached_plan
        
       
        
        # 3. 从数据库/缓存获取预生成的知识图谱
        from knowledge_base import get_course_db
        db = get_course_db()
        template_plan = db.get_plan_template(major, goal_zh)
        
        if template_plan:
            print(f"使用预生成方案: {major} - {goal_zh}")
            # 加入本地缓存
            cache_plan(major, goal, template_plan)
            return template_plan
        
        
        
        # 5. 兜底：使用大模型生成（用于自定义专业或复杂需求）
        print(f"无预生成方案，调用大模型生成: {major} - {goal_zh}")
        result = generate_plan_with_llm(major, goal_zh, job)
        plan_dict = result.dict()
        
        # 6. 将生成结果加入缓存
        cache_plan(major, goal, plan_dict)
        
        return plan_dict
    except Exception as e:
        # 打印具体错误到终端
        print(f"Backend error: {e}")
        # 返回具体的错误信息给前端
        raise HTTPException(status_code=500, detail=str(e))





# --- 3.5 推荐书籍接口 ---

@app.post("/api/recommend_books")
async def recommend_books(course: str = Form(...)):
    """
    根据课程名称推荐相关书籍
    """
    try:
        # 预设书籍推荐
        book_recommendations = {
            "Python": [
                {"title": "Python编程：从入门到实践", "author": "Eric Matthes", "publisher": "人民邮电出版社"},
                {"title": "流畅的Python", "author": "Luciano Ramalho", "publisher": "人民邮电出版社"},
                {"title": "Python核心编程", "author": "Wesley Chun", "publisher": "人民邮电出版社"},
                {"title": "Effective Python", "author": "Brett Slatkin", "publisher": "机械工业出版社"}
            ],
            "Java": [
                {"title": "Java核心技术 卷I", "author": "Cay S. Horstmann", "publisher": "机械工业出版社"},
                {"title": "深入理解Java虚拟机", "author": "周志明", "publisher": "机械工业出版社"},
                {"title": "Java编程思想", "author": "Bruce Eckel", "publisher": "机械工业出版社"},
                {"title": "Spring实战", "author": "Craig Walls", "publisher": "人民邮电出版社"}
            ],
            "数据结构": [
                {"title": "数据结构与算法分析", "author": "Mark Allen Weiss", "publisher": "机械工业出版社"},
                {"title": "算法导论", "author": "Thomas H. Cormen", "publisher": "机械工业出版社"},
                {"title": "数据结构（C语言版）", "author": "严蔚敏", "publisher": "清华大学出版社"},
                {"title": "算法图解", "author": "Aditya Bhargava", "publisher": "人民邮电出版社"}
            ],
            "计算机网络": [
                {"title": "计算机网络：自顶向下方法", "author": "James F. Kurose", "publisher": "人民邮电出版社"},
                {"title": "图解HTTP", "author": "上野宣", "publisher": "人民邮电出版社"},
                {"title": "TCP/IP详解 卷1", "author": "W. Richard Stevens", "publisher": "机械工业出版社"},
                {"title": "网络是怎样连接的", "author": "户根勤", "publisher": "人民邮电出版社"}
            ],
            "操作系统": [
                {"title": "深入理解计算机系统", "author": "Randal E. Bryant", "publisher": "机械工业出版社"},
                {"title": "现代操作系统", "author": "Andrew S. Tanenbaum", "publisher": "机械工业出版社"},
                {"title": "操作系统导论", "author": "Thomas W. Doeppner", "publisher": "机械工业出版社"},
                {"title": "Linux内核设计与实现", "author": "Robert Love", "publisher": "机械工业出版社"}
            ],
            "数据库": [
                {"title": "数据库系统概念", "author": "Abraham Silberschatz", "publisher": "机械工业出版社"},
                {"title": "MySQL技术内幕", "author": "姜承尧", "publisher": "机械工业出版社"},
                {"title": "SQL必知必会", "author": "Ben Forta", "publisher": "人民邮电出版社"},
                {"title": "Redis设计与实现", "author": "黄健宏", "publisher": "机械工业出版社"}
            ],
            "机器学习": [
                {"title": "机器学习", "author": "周志华", "publisher": "清华大学出版社"},
                {"title": "深度学习", "author": "Ian Goodfellow", "publisher": "人民邮电出版社"},
                {"title": "统计学习方法", "author": "李航", "publisher": "清华大学出版社"},
                {"title": "Hands-On Machine Learning", "author": "Aurélien Géron", "publisher": "O'Reilly"}
            ],
            "人工智能": [
                {"title": "人工智能：一种现代的方法", "author": "Stuart Russell", "publisher": "人民邮电出版社"},
                {"title": "AI算法导论", "author": "Dermot Turing", "publisher": "机械工业出版社"},
                {"title": "神经网络与深度学习", "author": "Michael Nielsen", "publisher": "人民邮电出版社"},
                {"title": "模式识别与机器学习", "author": "Christopher Bishop", "publisher": "Springer"}
            ],
            "高等数学": [
                {"title": "高等数学（第七版）", "author": "同济大学数学系", "publisher": "高等教育出版社"},
                {"title": "线性代数", "author": "同济大学数学系", "publisher": "高等教育出版社"},
                {"title": "概率论与数理统计", "author": "盛骤", "publisher": "高等教育出版社"},
                {"title": "数学分析", "author": "华东师范大学数学系", "publisher": "高等教育出版社"}
            ],
            "英语": [
                {"title": "新概念英语", "author": "L.G. Alexander", "publisher": "外语教学与研究出版社"},
                {"title": "剑桥雅思真题", "author": "Cambridge", "publisher": "剑桥大学出版社"},
                {"title": "托福词汇词根+联想记忆法", "author": "俞敏洪", "publisher": "群言出版社"},
                {"title": "GRE词汇精选", "author": "俞敏洪", "publisher": "群言出版社"}
            ],
            "考研": [
                {"title": "考研数学复习全书", "author": "李永乐", "publisher": "国家行政学院出版社"},
                {"title": "考研英语历年真题解析", "author": "张剑", "publisher": "世界图书出版公司"},
                {"title": "考研政治大纲解析", "author": "教育部考试中心", "publisher": "高等教育出版社"},
                {"title": "考研专业课历年真题", "author": "各高校", "publisher": "高等教育出版社"}
            ],
            "公务员": [
                {"title": "行测的思维", "author": "粉笔公考", "publisher": "新华出版社"},
                {"title": "申论的规矩", "author": "粉笔公考", "publisher": "新华出版社"},
                {"title": "历年真题详解", "author": "中公教育", "publisher": "人民日报出版社"},
                {"title": "面试的经验", "author": "粉笔公考", "publisher": "新华出版社"}
            ]
        }
        
        # 查找匹配的书籍
        matched_books = []
        for key, books in book_recommendations.items():
            if key.lower() in course.lower() or course.lower() in key.lower():
                matched_books.extend(books)
        
        # 如果没有找到匹配，返回通用推荐
        if not matched_books:
            matched_books = [
                {"title": f"《{course} 基础教程》", "author": "专业教材编写组", "publisher": "高等教育出版社"},
                {"title": f"《{course} 实战指南》", "author": "行业专家", "publisher": "机械工业出版社"},
                {"title": f"《{course} 从入门到精通》", "author": "资深工程师", "publisher": "电子工业出版社"},
                {"title": f"《{course} 深度解析》", "author": "高校教授", "publisher": "清华大学出版社"}
            ]
        
        return {"books": matched_books}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 4. 数据更新接口 ---

@app.post("/api/update_data")
async def update_data(
    data_type: str = Form(...),  # "jobs", "exams", "civil", "all"
    task_id: Optional[str] = Form(None)
):
    """
    手动触发数据更新
    - jobs: 仅更新职位数据
    - exams: 仅更新考研数据
    - civil: 仅更新考公数据
    - all: 更新所有数据
    """
    try:
        from scheduler import DataUpdater

        if data_type == "jobs":
            DataUpdater.update_jobs_only()
        elif data_type == "exams":
            DataUpdater.update_exams_only()
        elif data_type == "civil":
            DataUpdater.update_civil_only()
        elif data_type == "all":
            DataUpdater.update_all()
        else:
            raise HTTPException(status_code=400, detail="无效的数据类型")

        return {"status": "success", "message": f"{data_type} 数据更新完成"}
    except Exception as e:
        print(f"数据更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/update_status")
async def get_update_status():
    """获取数据更新状态"""
    try:
        from scheduler import get_scheduler

        scheduler = get_scheduler()
        tasks = scheduler.get_task_status()

        return {
            "status": "running",
            "tasks": tasks
        }
    except Exception as e:
        return {
            "status": "stopped",
            "error": str(e)
        }

# --- 5. 知识库检索接口 ---

@app.get("/api/search_knowledge")
async def search_knowledge(
    query: str,
    category: str = "all",  # "jobs", "exams", "courses", "all"
    limit: int = 10
):
    """
    搜索知识库中的数据
    用于RAG系统的检索增强
    """
    try:
        from knowledge_base import get_course_db

        db = get_course_db()
        results = []

        if category in ["all", "jobs"]:
            jobs = db.search_jobs(query, limit=limit)
            for job in jobs:
                job["type"] = "job"
                job["content"] = f"{job['title']} - {job['company']} - 薪资{job['salary_raw']}"
                results.append(job)

        if category in ["all", "exams"]:
            exams = db.search_exams(query, limit=limit)
            for exam in exams:
                exam["type"] = "exam"
                exam["content"] = f"{exam['school']} - {exam['major']} - 分数线{exam['score_line_raw']}"
                results.append(exam)

        return {
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        print(f"知识检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 5. 后台管理相关接口

# 获取用户列表（管理员专用）
@app.get("/api/admin/users")
def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查用户是否是管理员
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="只有管理员可以访问")
    
    users = db.query(User).all()
    return [{
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "major": user.major,
        "grade": user.grade,
        "role": user.role,
        "score": user.score
    } for user in users]

# 更新用户角色（管理员专用）
@app.put("/api/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查用户是否是管理员
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="只有管理员可以操作")
    
    # 解析 JSON 数据
    data = await request.json()
    role = data.get("role")
    
    if role is None:
        raise HTTPException(status_code=400, detail="角色不能为空")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.role = role
    db.commit()
    db.refresh(user)
    
    return {"message": "用户角色更新成功", "user": user}

# 获取帖子管理列表（管理员专用）
@app.get("/api/admin/posts")
def get_admin_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查用户是否是管理员
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="只有管理员可以访问")
    
    posts = db.query(Post).all()
    post_responses = []
    for post in posts:
        user = db.query(User).filter(User.id == post.user_id).first()
        username = user.username if user else "未知用户"
        
        post_responses.append({
            "id": post.id,
            "user_id": post.user_id,
            "username": username,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "create_time": post.create_time,
            "status": post.status
        })
    
    return post_responses

# 更新帖子状态（管理员专用）
@app.put("/api/admin/posts/{post_id}/status")
async def update_post_status(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查用户是否是管理员
    if current_user.role != 1:
        raise HTTPException(status_code=403, detail="只有管理员可以操作")
    
    # 解析 JSON 数据
    data = await request.json()
    status = data.get("status")
    
    if status is None:
        raise HTTPException(status_code=400, detail="状态不能为空")
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    post.status = status
    db.commit()
    db.refresh(post)
    
    return {"message": "帖子状态更新成功", "post": post}

# 6. 用户设置相关接口

# 获取用户设置
@app.get("/api/user/settings")
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 查找用户设置
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    # 如果没有设置，返回默认值
    if not settings:
        return {
            "home_background": "",
            "home_font_color": "#303133",
            "home_opacity": 0.8,
            "countdown_config": '{"title": "学期结束", "targetDate": "2026-06-30 23:59:59"}'
        }
    
    return {
        "home_background": settings.home_background,
        "home_font_color": settings.home_font_color,
        "home_opacity": settings.home_opacity,
        "countdown_config": settings.countdown_config
    }

# 更新用户设置
@app.put("/api/user/settings")
async def update_user_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 解析JSON数据
    data = await request.json()
    home_background = data.get("homeBackground", "")
    home_font_color = data.get("homeFontColor", "#303133")
    home_opacity = float(data.get("homeOpacity", 0.8))
    countdown_config = data.get("countdownConfig", '{"title": "学期结束", "targetDate": "2026-06-30 23:59:59"}')
    
    # 确保countdown_config是字符串格式
    if isinstance(countdown_config, dict):
        import json
        countdown_config = json.dumps(countdown_config)
    
    # 查找用户设置
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    # 如果没有设置，创建新的
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            home_background=home_background,
            home_font_color=home_font_color,
            home_opacity=home_opacity,
            countdown_config=countdown_config
        )
        db.add(settings)
    else:
        # 更新现有设置
        settings.home_background = home_background
        settings.home_font_color = home_font_color
        settings.home_opacity = home_opacity
        settings.countdown_config = countdown_config
    
    db.commit()
    db.refresh(settings)
    
    return {"message": "用户设置更新成功", "settings": settings}

# 上传背景图片
@app.post("/api/user/upload-background")
def upload_background(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 安全检查：确保是图片
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="文件必须是图片")
    
    # 生成唯一文件名，防止冲突
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 生成访问 URL
    url = f"/static/uploads/{unique_filename}"
    
    return {"url": url}

# --- 论坛相关接口 ---# 获取帖子列表
@app.get("/api/forum/posts")
def get_posts(
    db: Session = Depends(get_db)
):
    posts = db.query(Post).order_by(Post.create_time.desc()).all()
    return [{
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "username": post.user.username,
        "create_time": post.create_time,
        "view_count": post.view_count,
        "like_count": post.like_count
    } for post in posts]

# 获取帖子详情
@app.get("/api/forum/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 增加浏览量
    post.view_count += 1
    db.commit()
    
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "username": post.user.username,
        "create_time": post.create_time,
        "view_count": post.view_count,
        "like_count": post.like_count
    }

# 创建帖子
@app.post("/api/forum/posts")
async def create_post(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = await request.json()
    title = data.get("title")
    content = data.get("content")
    category = data.get("category")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="标题和内容不能为空")
    
    post = Post(
        title=title,
        content=content,
        category=category,
        user_id=current_user.id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "username": current_user.username,
        "create_time": post.create_time,
        "view_count": post.view_count,
        "like_count": post.like_count
    }

# 点赞帖子
@app.post("/api/forum/posts/{post_id}/like")
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查是否已经点赞
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()
    
    if like:
        # 取消点赞
        db.delete(like)
        post.like_count = max(0, post.like_count - 1)
    else:
        # 点赞
        like = Like(
            post_id=post_id,
            user_id=current_user.id
        )
        db.add(like)
        post.like_count += 1
    
    db.commit()
    
    return {"like_count": post.like_count}

# 获取用户点赞列表
@app.get("/api/forum/likes")
def get_user_likes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    likes = db.query(Like).filter(
        Like.user_id == current_user.id
    ).all()
    
    liked_posts = []
    for like in likes:
        post = db.query(Post).filter(Post.id == like.post_id).first()
        if post:
            liked_posts.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "category": post.category,
                "username": post.user.username if post.user else "未知用户",
                "create_time": post.create_time,
                "view_count": post.view_count,
                "like_count": post.like_count
            })
    
    return liked_posts

# 获取评论列表
@app.get("/api/forum/posts/{post_id}/comments")
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):
    comments = db.query(Comment).filter(
        Comment.post_id == post_id
    ).order_by(Comment.create_time.asc()).all()
    
    return [{
        "id": comment.id,
        "post_id": comment.post_id,
        "content": comment.content,
        "username": comment.user.username,
        "create_time": comment.create_time,
        "parent_id": comment.parent_id
    } for comment in comments]

# 创建评论
@app.post("/api/forum/comments")
async def create_comment(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = await request.json()
    post_id = data.get("post_id")
    content = data.get("content")
    parent_id = data.get("parent_id")
    
    if not post_id or not content:
        raise HTTPException(status_code=400, detail="帖子ID和评论内容不能为空")
    
    # 检查帖子是否存在
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    comment = Comment(
        post_id=post_id,
        content=content,
        user_id=current_user.id,
        parent_id=parent_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "content": comment.content,
        "username": current_user.username,
        "create_time": comment.create_time,
        "parent_id": comment.parent_id
    }

# 上传图片
@app.post("/api/forum/upload")
def upload_forum_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 安全检查：确保是图片
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="文件必须是图片")
    
    # 生成唯一文件名，防止冲突
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 生成访问 URL
    url = f"/static/uploads/{unique_filename}"
    
    return {"url": url}

# 更新路线步骤
@app.put("/api/travel/route-steps/{step_id}")
async def update_route_step(
    step_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = request.json()
    order = data.get("order")
    title = data.get("title")
    time = data.get("time")
    description = data.get("description")
    
    if not order or not title or not time:
        raise HTTPException(status_code=400, detail="顺序、标题和时间不能为空")
    
    # 检查步骤是否存在
    step = db.query(RouteStep).filter(RouteStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 更新步骤
    step.order = order
    step.title = title
    step.time = time
    step.description = description
    
    db.commit()
    db.refresh(step)
    
    return {
        "id": step.id,
        "route_id": step.route_id,
        "order": step.order,
        "title": step.title,
        "time": step.time,
        "description": step.description
    }

# 删除路线步骤
@app.delete("/api/travel/route-steps/{step_id}")
def delete_route_step(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 检查步骤是否存在
    step = db.query(RouteStep).filter(RouteStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")
    
    # 删除步骤
    db.delete(step)
    db.commit()
    
    return {"message": "步骤删除成功"}



if __name__ == "__main__":
    import uvicorn
    from scheduler import get_scheduler

    # 启动数据更新调度器
    sched = get_scheduler()
    sched.start()
    print("数据更新调度器已启动")

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        sched.stop()