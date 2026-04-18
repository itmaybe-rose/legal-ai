"""
数据库存储模块：使用SQLAlchemy同时支持MySQL和SQLite
用于存储爬取的课程、职位、考研考公数据
"""
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 尝试创建MySQL引擎
USE_MYSQL = False
engine = None

# 只使用内存缓存
memory_cache = {}

try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, Index
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker

    # MySQL配置 - 使用.env中的变量
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "campus_ai")

    # 尝试创建MySQL引擎
    if DB_PASSWORD:
        try:
            mysql_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            engine = create_engine(mysql_url, pool_pre_ping=True, pool_recycle=3600, echo=False)
            # 测试连接
            with engine.connect() as conn:
                pass
            USE_MYSQL = True
            print(f"[数据库] MySQL连接成功: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        except Exception as e:
            print(f"[数据库] MySQL连接失败，将使用SQLite: {e}")
            engine = None
    else:
        print("[数据库] 未配置MySQL密码，将使用SQLite")

except ImportError as e:
    print(f"[数据库] SQLAlchemy未安装: {e}")

# 如果没有MySQL，使用SQLite
if not USE_MYSQL:
    db_path = os.path.join(os.path.dirname(__file__), "data", "courses.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    print(f"[数据库] 使用SQLite: {db_path}")

# 创建基类
Base = declarative_base()

# SQLAlchemy 模型
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    salary_min = Column(Integer, default=0)
    salary_max = Column(Integer, default=0)
    salary_raw = Column(String(100))
    location = Column(String(100))
    experience = Column(String(50))
    education = Column(String(50))
    skills = Column(Text)
    posted_date = Column(String(50))
    source = Column(String(50))
    trend = Column(String(20))
    crawled_at = Column(String(50))
    updated_at = Column(String(50), default=datetime.now().isoformat)

    __table_args__ = (
        Index('idx_jobs_title', 'title'),
        Index('idx_jobs_company', 'company'),
    )

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school = Column(String(255), nullable=False)
    major = Column(String(255), nullable=False)
    direction = Column(String(255))
    exam_courses = Column(Text)
    score_line_min = Column(Integer, default=0)
    score_line_max = Column(Integer, default=0)
    score_line_raw = Column(String(100))
    enrollment_min = Column(Integer, default=0)
    enrollment_max = Column(Integer, default=0)
    enrollment_raw = Column(String(100))
    difficulty = Column(String(20))
    source = Column(String(50))
    crawled_at = Column(String(50))
    updated_at = Column(String(50), default=datetime.now().isoformat)

    __table_args__ = (
        Index('idx_exams_school', 'school'),
        Index('idx_exams_major', 'major'),
    )

class CivilExam(Base):
    __tablename__ = "civil_exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    level = Column(String(50))
    requirement = Column(Text)
    exam_type = Column(String(50))
    source = Column(String(50))
    crawled_at = Column(String(50))
    updated_at = Column(String(50), default=datetime.now().isoformat)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    level = Column(String(50))
    provider = Column(String(100))
    url = Column(String(500))
    update_date = Column(String(50))
    skills = Column(Text)
    crawled_at = Column(String(50))
    updated_at = Column(String(50), default=datetime.now().isoformat)

    __table_args__ = (
        Index('idx_courses_category', 'category'),
    )

class PlanTemplate(Base):
    __tablename__ = 'plan_templates'
    id = Column(Integer, primary_key=True)
    major = Column(String(100), index=True) # 专业
    goal = Column(String(50), index=True) # 目标 (考研/考公/就业)
    graph_json = Column(Text) # 预生成的知识图谱 JSON
    updated_at = Column(String(50))
    
    # 这样，用户请求时直接 SELECT graph_json WHERE major='计算机' AND goal='考研'

# 创建表
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# 内存缓存作为Redis的备选
memory_cache = {}

class CourseDatabase:
    """课程数据库"""

    def __init__(self):
        self.session = Session()

    def insert_jobs(self, jobs: List[Dict]) -> int:
        """插入职位数据"""
        count = 0
        for job in jobs:
            try:
                job_obj = Job(
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    salary_min=job.get("salary", {}).get("min", 0),
                    salary_max=job.get("salary", {}).get("max", 0),
                    salary_raw=job.get("salary", {}).get("raw", ""),
                    location=job.get("location", ""),
                    experience=job.get("experience", ""),
                    education=job.get("education", ""),
                    skills=json.dumps(job.get("skills", []), ensure_ascii=False),
                    posted_date=job.get("posted_date", ""),
                    source=job.get("source", ""),
                    trend=job.get("trend", ""),
                    crawled_at=job.get("crawled_at", datetime.now().isoformat())
                )
                self.session.add(job_obj)
                count += 1
            except Exception as e:
                print(f"插入职位失败: {e}")

        self.session.commit()
        return count

    def insert_exams(self, exams: List[Dict]) -> int:
        """插入考研数据"""
        count = 0
        for exam in exams:
            try:
                exam_obj = Exam(
                    school=exam.get("school", ""),
                    major=exam.get("major", ""),
                    direction=exam.get("direction", ""),
                    exam_courses=json.dumps(exam.get("exam_courses", []), ensure_ascii=False),
                    score_line_min=exam.get("score_line", {}).get("min", 0),
                    score_line_max=exam.get("score_line", {}).get("max", 0),
                    score_line_raw=exam.get("score_line", {}).get("raw", ""),
                    enrollment_min=exam.get("enrollment", {}).get("min", 0),
                    enrollment_max=exam.get("enrollment", {}).get("max", 0),
                    enrollment_raw=exam.get("enrollment", {}).get("raw", ""),
                    difficulty=exam.get("difficulty", ""),
                    source=exam.get("source", ""),
                    crawled_at=exam.get("crawled_at", datetime.now().isoformat())
                )
                self.session.add(exam_obj)
                count += 1
            except Exception as e:
                print(f"插入考研数据失败: {e}")

        self.session.commit()
        return count

    def insert_civil_exams(self, civil_exams: List[Dict]) -> int:
        """插入考公数据"""
        count = 0
        for info in civil_exams:
            try:
                civil_obj = CivilExam(
                    department=info.get("department", ""),
                    position=info.get("position", ""),
                    level=info.get("level", ""),
                    requirement=info.get("requirement", ""),
                    exam_type=info.get("exam_type", ""),
                    source=info.get("source", ""),
                    crawled_at=info.get("crawled_at", datetime.now().isoformat())
                )
                self.session.add(civil_obj)
                count += 1
            except Exception as e:
                print(f"插入考公数据失败: {e}")

        self.session.commit()
        return count

    def insert_courses(self, courses: List[Dict]) -> int:
        """插入课程数据"""
        count = 0
        for course in courses:
            try:
                course_obj = Course(
                    title=course.get("title", ""),
                    description=course.get("description", ""),
                    category=course.get("category", ""),
                    level=course.get("level", ""),
                    provider=course.get("provider", ""),
                    url=course.get("url", ""),
                    update_date=course.get("update_date", ""),
                    skills=json.dumps(course.get("skills", []), ensure_ascii=False),
                    crawled_at=course.get("crawled_at", datetime.now().isoformat())
                )
                self.session.add(course_obj)
                count += 1
            except Exception as e:
                print(f"插入课程失败: {e}")

        self.session.commit()
        return count

    def search_jobs(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索职位"""
        from sqlalchemy import or_
        results = self.session.query(Job).filter(
            or_(
                Job.title.like(f"%{keyword}%"),
                Job.skills.like(f"%{keyword}%"),
                Job.company.like(f"%{keyword}%")
            )
        ).order_by(Job.crawled_at.desc()).limit(limit).all()

        jobs = []
        for job in results:
            jobs.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_raw": job.salary_raw,
                "location": job.location,
                "experience": job.experience,
                "education": job.education,
                "skills": json.loads(job.skills) if job.skills else [],
                "posted_date": job.posted_date,
                "source": job.source,
                "trend": job.trend,
                "crawled_at": job.crawled_at
            })
        return jobs

    def search_exams(self, major: str, limit: int = 10) -> List[Dict]:
        """搜索考研信息"""
        from sqlalchemy import or_
        results = self.session.query(Exam).filter(
            or_(
                Exam.major.like(f"%{major}%"),
                Exam.school.like(f"%{major}%")
            )
        ).order_by(Exam.score_line_min.desc()).limit(limit).all()

        exams = []
        for exam in results:
            exams.append({
                "id": exam.id,
                "school": exam.school,
                "major": exam.major,
                "direction": exam.direction,
                "exam_courses": json.loads(exam.exam_courses) if exam.exam_courses else [],
                "score_line_min": exam.score_line_min,
                "score_line_max": exam.score_line_max,
                "score_line_raw": exam.score_line_raw,
                "enrollment_min": exam.enrollment_min,
                "enrollment_max": exam.enrollment_max,
                "enrollment_raw": exam.enrollment_raw,
                "difficulty": exam.difficulty,
                "source": exam.source,
                "crawled_at": exam.crawled_at
            })
        return exams

    def get_all_jobs(self, limit: int = 100) -> List[Dict]:
        """获取所有职位"""
        results = self.session.query(Job).order_by(Job.crawled_at.desc()).limit(limit).all()
        jobs = []
        for job in results:
            jobs.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_raw": job.salary_raw,
                "location": job.location,
                "skills": json.loads(job.skills) if job.skills else [],
                "trend": job.trend
            })
        return jobs

    def get_all_exams(self, limit: int = 100) -> List[Dict]:
        """获取所有考研信息"""
        results = self.session.query(Exam).order_by(Exam.crawled_at.desc()).limit(limit).all()
        exams = []
        for exam in results:
            exams.append({
                "id": exam.id,
                "school": exam.school,
                "major": exam.major,
                "direction": exam.direction,
                "score_line_raw": exam.score_line_raw,
                "difficulty": exam.difficulty
            })
        return exams

    def clear_old_data(self, days: int = 30):
        """清理旧数据"""
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        self.session.query(Job).filter(Job.crawled_at < cutoff_date).delete()
        self.session.query(Exam).filter(Exam.crawled_at < cutoff_date).delete()
        self.session.query(CivilExam).filter(CivilExam.crawled_at < cutoff_date).delete()
        self.session.query(Course).filter(Course.crawled_at < cutoff_date).delete()

        self.session.commit()

    def get_plan_template(self, major: str, goal: str) -> Dict:
        """获取预设的知识图谱模板"""
        # 先尝试从内存缓存获取
        cache_key = f"plan:{major}:{goal}"
        
        if cache_key in memory_cache:
            return memory_cache[cache_key]
        
        # 从数据库获取
        try:
            template = self.session.query(PlanTemplate).filter(
                PlanTemplate.major == major,
                PlanTemplate.goal == goal
            ).first()
            
            if template:
                plan_data = json.loads(template.graph_json)
                # 存入内存缓存
                memory_cache[cache_key] = plan_data
                return plan_data
        except Exception as e:
            print(f"从数据库获取模板失败: {e}")
        
        return None

    def save_plan_template(self, major: str, goal: str, graph_json: Dict):
        """保存知识图谱模板"""
        try:
            # 检查是否已存在
            existing = self.session.query(PlanTemplate).filter(
                PlanTemplate.major == major,
                PlanTemplate.goal == goal
            ).first()
            
            if existing:
                # 更新
                existing.graph_json = json.dumps(graph_json, ensure_ascii=False)
                existing.updated_at = datetime.now().isoformat()
            else:
                # 新增
                new_template = PlanTemplate(
                    major=major,
                    goal=goal,
                    graph_json=json.dumps(graph_json, ensure_ascii=False),
                    updated_at=datetime.now().isoformat()
                )
                self.session.add(new_template)
            
            self.session.commit()
            
            # 更新内存缓存
            cache_key = f"plan:{major}:{goal}"
            memory_cache[cache_key] = graph_json
            
            print(f"保存模板成功: {major} - {goal}")
        except Exception as e:
            print(f"保存模板失败: {e}")

# 全局数据库实例
course_db = None

def get_course_db() -> CourseDatabase:
    """获取课程数据库实例"""
    global course_db
    if course_db is None:
        course_db = CourseDatabase()
    return course_db

if __name__ == "__main__":
    # 测试数据库
    db = CourseDatabase()

    # 测试插入
    test_jobs = [
        {
            "title": "Java工程师",
            "company": "字节跳动",
            "salary": {"min": 20000, "max": 40000, "raw": "20K-40K"},
            "location": "北京",
            "experience": "3-5年",
            "education": "本科",
            "skills": ["Java", "Spring", "MySQL"],
            "posted_date": "3天前",
            "source": "zhipin",
            "trend": "热门"
        }
    ]

    count = db.insert_jobs(test_jobs)
    print(f"插入 {count} 条职位")

    # 测试搜索
    results = db.search_jobs("Java")
    print(f"搜索到 {len(results)} 条结果")

    # 测试模板保存和读取
    test_template = {
        "summary": "测试模板",
        "skill_tree": [],
        "resources": [],
        "job_market": []
    }
    db.save_plan_template("计算机科学", "就业", test_template)
    loaded_template = db.get_plan_template("计算机科学", "就业")
    print(f"加载模板成功: {loaded_template}")