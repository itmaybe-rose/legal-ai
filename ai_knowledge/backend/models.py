from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100)) # 存加密后的密码

    # --- 👇 新增的用户档案字段 ---
    name = Column(String, default="")       # 昵称
    major = Column(String, default="")     # 专业
    grade = Column(String, default="")     # 年级
    avatar = Column(String, default="")    # 头像 URL

# --- 👇 新增的代码：专业表 ---
class Major(Base):
    __tablename__ = "majors" 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True) 
    college = Column(String(50), default="")     