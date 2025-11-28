from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
from .config import Config
from .models import TaskNotify

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
        return None, 0

    # 在删除前，计算该分类相关的 task_notifies 数量
    notifies_count = db.query(models.TaskNotify).filter(
        models.TaskNotify.category_id == category_id,
        models.TaskNotify.user_id == user_id).count()

    # 删除分类（由于设置了级联删除，关联的项目和进度也会自动删除）
    db.delete(db_category)
    db.commit()

    return db_category, notifies_count


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
        return None, 0

    # 在删除前，计算该项目相关的 task_notifies 数量
    notifies_count = db.query(models.TaskNotify).filter(
        models.TaskNotify.item_id == item_id,
        models.TaskNotify.user_id == user_id).count()

    # 删除项目（由于设置了级联删除，关联的进度也会自动删除）
    db.delete(db_item)
    db.commit()

    return db_item, notifies_count


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


# 此函數不分user_id，所以不檢查
def get_progress_details(db: Session, category_id: int, item_id: int,
                         progress_id: int):
    """获取分类、项目和进度的详细信息"""
    try:
        # 查询分类
        category = db.query(models.TaskCategory).filter(
            models.TaskCategory.id == category_id).first()

        # 查询项目
        item = db.query(
            models.TaskItem).filter(models.TaskItem.id == item_id).first()

        # 查询进度
        progress = db.query(models.TaskProgress).filter(
            models.TaskProgress.id == progress_id).first()

        # 如果任何一个ID不存在，返回None
        if not category or not item or not progress:
            return None

        # 返回所需信息
        return {
            "category_name": category.category_name,
            "item_name": item.item_name,
            "progress_name": progress.progress_name,
            "progress_content": progress.content
        }
    except Exception as e:
        print(f"Error getting progress details: {str(e)}")
        return None


def create_task_notify(db: Session,
                       notify: schemas.TaskNotifyCreate,
                       user_id: int,
                       task_notify_service: TaskNotify = None):
    """创建新的任务通知"""
    db_notify = models.TaskNotify(user_id=user_id,
                                  category_id=notify.category_id,
                                  item_id=notify.item_id,
                                  progress_id=notify.progress_id,
                                  start_at=notify.start_at,
                                  stop_at=notify.stop_at,
                                  run_mode=notify.run_mode,
                                  run_code=notify.run_code,
                                  time_at=notify.time_at,
                                  week_at=notify.week_at)
    db.add(db_notify)
    db.commit()
    db.refresh(db_notify)

    # # 检查是否应该加载到内存
    # if task_notify_service and task_notify_service.should_load_notify(
    #         notify_dict):
    #     task_notify_service.add_notify(notify_dict)

    # 只要服務存在就加载到内存
    # 因為task_notify_serviceo只在main執行時才自動初始化，如果在服務存在時不加入
    # 會導致新增後的通知無法被執行(除非管理員在前端關閉又重新啟動，'🔔' : '🔕'，或者在管理員專用的選單中選擇重新讀取通知)
    if task_notify_service:
        # 获取用户信息
        user = db.query(models.User).filter(models.User.id == user_id).first()
        # 转换为字典格式
        notify_dict = db_notify.__dict__.copy()
        # 添加username属性
        notify_dict['username'] = user.username if user else None
        task_notify_service.add_notify(notify_dict)
    return db_notify


def update_task_notify(db: Session,
                       notify_id: int,
                       notify: schemas.TaskNotifyUpdate,
                       user_id: int,
                       task_notify_service: TaskNotify = None):
    """更新任务通知"""
    # 查找通知
    db_notify = db.query(models.TaskNotify).filter(
        models.TaskNotify.id == notify_id,
        models.TaskNotify.user_id == user_id).first()
    if not db_notify:
        return None

    # 更新通知信息
    if notify.start_at is not None:
        db_notify.start_at = notify.start_at
    if notify.stop_at is not None:
        db_notify.stop_at = notify.stop_at
    if notify.run_mode is not None:
        db_notify.run_mode = notify.run_mode
    if notify.run_code is not None:
        db_notify.run_code = notify.run_code
    if notify.time_at is not None:
        db_notify.time_at = notify.time_at
    if notify.week_at is not None:
        db_notify.week_at = notify.week_at

    db_notify.last_executed = None

    db.commit()
    db.refresh(db_notify)

    if task_notify_service:
        # 获取用户信息
        user = db.query(models.User).filter(models.User.id == user_id).first()
        # 转换为字典格式
        notify_dict = db_notify.__dict__.copy()
        # 添加username属性
        notify_dict['username'] = user.username if user else None
        task_notify_service.remove_notify(notify_dict['id'])
        task_notify_service.add_notify(notify_dict)
    return db_notify


def delete_task_notify(db: Session,
                       notify_id: int,
                       user_id: int,
                       task_notify_service: TaskNotify = None):
    """删除任务通知"""
    # 查找通知
    db_notify = db.query(models.TaskNotify).filter(
        models.TaskNotify.id == notify_id,
        models.TaskNotify.user_id == user_id).first()
    if not db_notify:
        return None
    # 删除通知
    db.delete(db_notify)
    db.commit()

    if task_notify_service:
        task_notify_service.remove_notify(notify_id)

    return db_notify


def reset_last_executed(db: Session, user_id: int = None):
    """重置最后执行时间"""
    query = db.query(models.TaskNotify).filter(
        models.TaskNotify.last_executed.isnot(None))

    if user_id != 0:
        query = query.filter(models.TaskNotify.user_id == user_id)

    updated = query.update({'last_executed': None})
    db.commit()
    return updated


def delete_notifies(db: Session, user_id: int):
    """删除用户的所有通知"""
    try:
        # 如果 user_id 为 0，删除所有通知
        if user_id == 0:
            deleted_count = db.query(models.TaskNotify).count()
            db.query(models.TaskNotify).delete()
        else:
            # 删除指定用户的通知
            deleted_count = db.query(models.TaskNotify).filter(
                models.TaskNotify.user_id == user_id).count()
            db.query(models.TaskNotify).filter(
                models.TaskNotify.user_id == user_id).delete()

        db.commit()
        return deleted_count
    except Exception as e:
        print(f"Error deleting notifies: {str(e)}")
        db.rollback()
        return 0
