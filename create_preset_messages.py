# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Message

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 数据库URL - 与create_preset_users.py保持一致
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_rwfI5m8ihqZE@ep-flat-moon-adc7i78o-pooler.c-2.us-east-1.aws.neon.tech/board?sslmode=require&channel_binding=require')

# 创建数据库连接
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库会话
db = SessionLocal()

try:
    # 预设留言数据
    preset_messages = [
        {
            "content": "这是第一条留言示例",
            "image_url": None,
            "user_id": 3
        },
        {
            "content": "今天天气真不错，适合出门走走",
            "image_url": None,
            "user_id": 3
        },
        {
            "content": "分享一个有趣的链接：https://example.com",
            "image_url": None,
            "user_id": 3
        },
        {
            "content": "有人想一起周末去看电影吗？",
            "image_url": None,
            "user_id": 3
        },
        {
            "content": "这是第五条留言，希望对大家有帮助！",
            "image_url": None,
            "user_id": 3
        }
    ]
    
    for message_data in preset_messages:
        # 创建新留言
        new_message = Message(
            content=message_data["content"],
            image_url=message_data["image_url"],
            user_id=message_data["user_id"]
        )
        
        db.add(new_message)
        print(f"成功创建留言: '{message_data['content']}'")
    
    # 提交更改
    db.commit()
    print("所有预设留言创建完成")
    
except Exception as e:
    print(f"创建留言时出错: {e}")
    db.rollback()
    
finally:
    db.close()
