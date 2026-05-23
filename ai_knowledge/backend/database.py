from sqlalchemy import create_engine # 创建数据库引擎
from sqlalchemy.ext.declarative import declarative_base # 声明式基类
from sqlalchemy.orm import sessionmaker # 会话工厂类
import os
from dotenv import load_dotenv
 


load_dotenv()

 
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

 

engine = create_engine(
    DATABASE_URL,
    # 生产环境建议加上连接池配置，防止连接断开
    pool_pre_ping=True, # 每次从连接池获取连接时都检查连接是否有效
    pool_recycle=3600 # 连接池中的连接在3600秒后自动回收
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # 会话工厂类，用于创建会话实例
Base = declarative_base() # 声明式基类，用于创建数据库模型类

def get_db():
    """
    获取数据库会话实例
    """
    db = SessionLocal()
    try:
        yield db # 返回数据库话实例
    finally:
        db.close() # 关闭数据库会话