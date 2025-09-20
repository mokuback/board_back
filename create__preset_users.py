import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.auth import get_password_hash

# 数据库URL - 根据您的实际配置修改
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_rwfI5m8ihqZE@ep-flat-moon-adc7i78o-pooler.c-2.us-east-1.aws.neon.tech/board?sslmode=require&channel_binding=require')

# 创建数据库连接
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建数据库会话
db = SessionLocal()

try:
    # 预设用户数据
    preset_users = [
        {
            "username": "U8f527158a06064c7bcf036bd938ddf4c",
            "password": "admin123",
            "is_admin": True
        },
        {
            "username": "user",
            "password": "user123",
            "is_admin": False
        },
        {
            "username": "test",
            "password": "test123",
            "is_admin": False
        },        
        {
            "username": "coper",
            "password": "coper6019",
            "is_admin": False
        },         
    ]
    
    for user_data in preset_users:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        
        if existing_user:
            print(f"用户 '{user_data['username']}' 已存在，跳过创建")
            continue
        
        # 创建新用户
        hashed_password = get_password_hash(user_data["password"])
        new_user = User(
            username=user_data["username"],
            password_hash=hashed_password,
            is_admin=user_data["is_admin"]
        )
        
        db.add(new_user)
        print(f"成功创建用户 '{user_data['username']}'")
    
    # 提交更改
    db.commit()
    print("所有预设用户创建完成")
    
except Exception as e:
    print(f"创建用户时出错: {e}")
    db.rollback()
    
finally:
    db.close()
