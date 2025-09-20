from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
from .config import Config

# 配置 Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Message).order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()

async def create_user_message(db: Session, message: schemas.MessageCreate, user_id: int, file=None):
    """
    创建用户消息，包含内容验证和文件上传功能
    """
    try:
        # 验证内容
        if not message.content or len(message.content.strip()) == 0:
            raise ValueError("Content cannot be empty")

        # 处理文件上传
        image_url = None
        if file:
            image_url = await upload_image_to_cloudinary(file)
            if not image_url:
                raise ValueError("Failed to upload image")

        # 创建消息对象
        message_data = {
            "content": message.content,
            "user_id": user_id,
            "image_url": image_url
        }
        
        # 创建消息
        db_message = models.Message(**message_data)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        return db_message

    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error creating message: {str(e)}")
        return None


def delete_message(db: Session, message_id: int):
    """
    删除消息，如果消息包含图片则同时删除Cloudinary上的图片
    """
    try:
        # 获取要删除的消息
        message = db.query(models.Message).filter(models.Message.id == message_id).first()
        if not message:
            return None

        # 如果消息包含图片，从Cloudinary删除
        if message.image_url:
            try:
                # 从URL中提取public_id
                public_id = message.image_url.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(public_id)
            except Exception as e:
                print(f"Error deleting image from Cloudinary: {str(e)}")

        # 删除数据库中的消息记录
        db.delete(message)
        db.commit()
        
        return message

    except Exception as e:
        print(f"Error deleting message: {str(e)}")
        db.rollback()
        return None

# def delete_message(db: Session, message_id: int):
#     message = db.query(models.Message).filter(models.Message.id == message_id).first()
#     if message:
#         db.delete(message)
#         db.commit()
#     return message

async def upload_image_to_cloudinary(file):
    try:
        # 读取文件内容（异步）
        file_content = await file.read()
        
        # 上传图片到Cloudinary
        upload_result = cloudinary.uploader.upload(file_content)
        return upload_result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return None
