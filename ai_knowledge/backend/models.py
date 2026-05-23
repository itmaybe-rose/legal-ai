from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100)) # 存加密后的密码

    # --- 👇 新增的用户档案字段 ---
    name = Column(String(100), default="")       # 昵称
    major = Column(String(100), default="")     # 专业
    grade = Column(String(50), default="")     # 年级
    avatar = Column(String(500), default="")    # 头像 URL
    role = Column(Integer, default=0, index=True)       # 0:学生, 1:管理员
    score = Column(Integer, default=0, index=True)      # 积分
    create_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # 注册时间
    
    # --- 👇 新增的关系定义 ---
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)

# --- 👇 新增的代码：专业表 ---
class Major(Base):
    __tablename__ = "majors" 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True) 
    college = Column(String(50), default="")     

# --- 👇 新增的代码：帖子表 ---
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="讨论", index=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    create_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(Integer, default=0, index=True)  # 0:正常, 1:审核, 2:违规
    
    # --- 👇 新增的关系定义 ---
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    likes = relationship("Like", back_populates="post")

# --- 👇 新增的代码：评论表 ---
class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(Integer, default=0)  # 0:正常, 1:审核, 2:违规
    
    # --- 👇 新增的关系定义 ---
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

# --- 👇 新增的代码：点赞表 ---
class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # --- 👇 新增的关系定义 ---
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")
    
    # 确保一个用户只能点赞一个帖子一次
    __table_args__ = (
        {'extend_existing': True},
    )

# --- 👇 新增的代码：用户设置表 ---
class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    home_background = Column(String(255), default="")
    home_font_color = Column(String(20), default="#303133")
    home_opacity = Column(Float, default=0.8)
    countdown_config = Column(Text, default='{"title": "学期结束", "targetDate": "2026-06-30 23:59:59"}')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- 👇 新增的关系定义 ---
    user = relationship("User", back_populates="settings")

# --- 👇 新增的代码：旅游相关表 ---
class City(Base):
    __tablename__ = "cities"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    color = Column(String(20), default="#409eff")
    transport = Column(String(100), default="")
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Spot(Base):
    __tablename__ = "spots"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(String(50), ForeignKey("cities.id"))
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # landmark, food, transport
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    desc = Column(Text, default="")
    price = Column(String(50), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    duration = Column(String(50), default="")
    difficulty = Column(String(20), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class RouteStep(Base):
    __tablename__ = "route_steps"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    order = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    time = Column(String(50), default="")
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# --- 👇 课程表相关模型 ---
class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_url = Column(String(255), default="")  # 上传的课程表图片URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系定义
    user = relationship("User", backref="schedules")
    courses = relationship("Course", back_populates="schedule")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    name = Column(String(100), nullable=False)  # 课程名称
    day_of_week = Column(Integer, nullable=False)  # 星期几 (1-7)
    period = Column(String(50), nullable=False)  # 上课节次 (如 "1-2节")
    time_start = Column(String(20))  # 开始时间 (如 "08:00")
    time_end = Column(String(20))  # 结束时间 (如 "09:40")
    classroom = Column(String(100))  # 教室
    teacher = Column(String(100))  # 教师
    color = Column(String(20), default="#409eff")  # 课程颜色
    
    # 关系定义
    schedule = relationship("Schedule", back_populates="courses")
