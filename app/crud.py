from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
from .config import Config

# 配置 Cloudinary
cloudinary.config(cloud_name=Config.CLOUDINARY_CLOUD_NAME,
                  api_key=Config.CLOUDINARY_API_KEY,
                  api_secret=Config.CLOUDINARY_API_SECRET)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(
        models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username,
                          password_hash=hashed_password,
                          is_admin=user.is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_login_record(db: Session, user_id: int):
    login_record = models.LoginRecord(user_id=user_id)
    db.add(login_record)
    db.commit()
    return login_record


def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Message).order_by(
        models.Message.created_at.desc()).offset(skip).limit(limit).all()


async def create_user_message(db: Session,
                              message: schemas.MessageCreate,
                              user_id: int,
                              file=None):
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
        message = db.query(
            models.Message).filter(models.Message.id == message_id).first()
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


def create_task_category(db: Session, category: schemas.TaskCategoryCreate,
                         user_id: int):
    """创建新的任务分类"""
    db_category = models.TaskCategory(user_id=user_id,
                                      category_name=category.category_name,
                                      content=category.content)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_task_category(db: Session, category_id: int,
                         category: schemas.TaskCategoryUpdate, user_id: int):
    """更新任务分类"""
    # 查找分类
    db_category = db.query(models.TaskCategory).filter(
        models.TaskCategory.id == category_id,
        models.TaskCategory.user_id == user_id).first()

    if not db_category:
        return None

    # 更新分类信息
    db_category.category_name = category.category_name
    db_category.content = category.content

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_task_category(db: Session, category_id: int, user_id: int):
    """删除任务分类及其关联的所有项目和进度"""
    # 查找分类
    db_category = db.query(models.TaskCategory).filter(
        models.TaskCategory.id == category_id,
        models.TaskCategory.user_id == user_id).first()
    if not db_category:
        return None

    # 删除分类（由于设置了级联删除，关联的项目和进度也会自动删除）
    db.delete(db_category)
    db.commit()

    return db_category


def create_task_item(db: Session, item: schemas.TaskItemCreate, user_id: int):
    """创建新的任务项"""
    db_item = models.TaskItem(user_id=user_id,
                              category_id=item.category_id,
                              item_name=item.item_name,
                              content=item.content,
                              item_at=item.item_at)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_task_item(db: Session, item_id: int, item: schemas.TaskItemUpdate,
                     user_id: int):
    """更新任务项目"""
    # 查找项目
    db_item = db.query(models.TaskItem).filter(
        models.TaskItem.id == item_id,
        models.TaskItem.user_id == user_id).first()
    if not db_item:
        return None

    # 更新项目信息
    db_item.item_name = item.item_name
    db_item.content = item.content
    if item.item_at:
        db_item.item_at = item.item_at

    db.commit()
    db.refresh(db_item)
    return db_item


def delete_task_item(db: Session, item_id: int, user_id: int):
    """删除任务项目及其关联的所有进度"""
    # 查找项目
    db_item = db.query(models.TaskItem).filter(
        models.TaskItem.id == item_id,
        models.TaskItem.user_id == user_id).first()
    if not db_item:
        return None
    # 删除项目（由于设置了级联删除，关联的进度也会自动删除）
    db.delete(db_item)
    db.commit()

    return db_item


def create_task_progress(db: Session, progress: schemas.TaskProgressCreate,
                         user_id: int):
    """创建新的任务进度"""
    db_progress = models.TaskProgress(user_id=user_id,
                                      item_id=progress.item_id,
                                      progress_name=progress.progress_name,
                                      content=progress.content,
                                      progress_at=progress.progress_at,
                                      status=progress.status)
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def update_task_progress(db: Session, progress_id: int,
                         progress: schemas.TaskProgressUpdate, user_id: int):
    """更新任务进度"""
    # 查找进度
    db_progress = db.query(models.TaskProgress).filter(
        models.TaskProgress.id == progress_id,
        models.TaskProgress.user_id == user_id).first()
    if not db_progress:
        return None

    # 更新进度信息
    db_progress.progress_name = progress.progress_name
    db_progress.content = progress.content
    if progress.progress_at:
        db_progress.progress_at = progress.progress_at
    if progress.status is not None:
        db_progress.status = progress.status

    db.commit()
    db.refresh(db_progress)
    return db_progress


def delete_task_progress(db: Session, progress_id: int, user_id: int):
    """删除任务进度"""
    # 打印调试信息
    print(f"Deleting progress - ID: {progress_id}, User ID: {user_id}")

    # 查找进度
    db_progress = db.query(models.TaskProgress).filter(
        models.TaskProgress.id == progress_id,
        models.TaskProgress.user_id == user_id).first()
    if not db_progress:
        print(f"Progress with ID {progress_id} not found")
        return None

    # 删除进度
    db.delete(db_progress)
    db.commit()

    return db_progress
