from database import engine
from models import Like

# 创建点赞表
Like.__table__.create(bind=engine, checkfirst=True)
print("点赞表创建成功")
