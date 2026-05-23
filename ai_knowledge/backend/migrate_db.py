from database import engine
from sqlalchemy import text, inspect

# 检查现有的列
inspector = inspect(engine)
existing_columns = [col['name'] for col in inspector.get_columns('users')]
print(f"users表现有列: {existing_columns}")

with engine.connect() as conn:
    # 添加create_time字段
    if 'create_time' not in existing_columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP"))
        print("成功添加create_time字段到users表")
    else:
        print("create_time字段已存在")
    
    # 添加role字段
    if 'role' not in existing_columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN role INT DEFAULT 0"))
        print("成功添加role字段到users表")
    else:
        print("role字段已存在")
    
    # 添加score字段
    if 'score' not in existing_columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN score INT DEFAULT 0"))
        print("成功添加score字段到users表")
    else:
        print("score字段已存在")

    conn.commit()
    print("数据库迁移完成")