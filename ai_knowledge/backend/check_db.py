from database import engine
from sqlalchemy import inspect

# 检查数据库表结构
inspector = inspect(engine)

# 获取users表的列信息
print("Users table columns:")
columns = inspector.get_columns('users')
for column in columns:
    print(f"{column['name']}: {column['type']}")

print("\nAll tables in database:")
tables = inspector.get_table_names()
for table in tables:
    print(table)