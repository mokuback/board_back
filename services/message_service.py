# board_back/services/message_service.py
import os
import cloudinary
from cloudinary.uploader import destroy
from services.base_service import BaseService
from models.message import Message
from utils.logger import logger
from utils.validators import MessageModel

# 初始化 Cloudinary 配置
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

class MessageService(BaseService):
    def add_message(self, content, image_url=None, user_id=None):
        """添加新留言"""
        try:
            # 验证输入数据
            message_data = MessageModel(content=content, image_url=image_url, user_id=user_id)
            
            def _add_operation(session):
                message = Message(**message_data.model_dump())
                session.add(message)
                session.refresh(message)
                logger.info(f"Message added with ID: {message.id}")
                return message.to_dict()
            
            return self._execute_with_session(_add_operation)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}")
            return None
    
    def get_all_messages(self):
        """获取所有留言"""
        def _get_operation(session):
            messages = session.query(Message).order_by(Message.created_at.desc()).all()
            return [message.to_dict() for message in messages]
        
        try:
            return self._execute_with_session(_get_operation)
        except Exception as e:
            logger.error(f"Failed to get messages: {str(e)}")
            return []
    
    def get_messages_with_pagination(self, page=1, per_page=10):
        """分页获取留言"""
        def _get_operation(session):
            messages = session.query(Message).order_by(Message.created_at.desc())
            pagination = messages.paginate(page=page, per_page=per_page, error_out=False)
            return {
                'items': [message.to_dict() for message in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page
            }
        
        try:
            return self._execute_with_session(_get_operation)
        except Exception as e:
            logger.error(f"Failed to get messages with pagination: {str(e)}")
            return {
                'items': [],
                'total': 0,
                'pages': 0,
                'current_page': page
            }
    
    def get_messages_by_user(self, user_id):
        """获取指定用户的所有留言"""
        def _get_operation(session):
            messages = session.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).all()
            return [message.to_dict() for message in messages]
        
        try:
            return self._execute_with_session(_get_operation)
        except Exception as e:
            logger.error(f"Failed to get messages by user {user_id}: {str(e)}")
            return []
    
    def delete_message(self, message_id):
        """删除留言及其关联的图片"""
        def _delete_operation(session):
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                # 如果有图片，从Cloudinary删除
                if message.image_url:
                    self._delete_from_cloudinary(message.image_url)
                session.delete(message)
                logger.info(f"Message deleted with ID: {message_id}")
                return True
            return False
        
        try:
            return self._execute_with_session(_delete_operation)
        except Exception as e:
            logger.error(f"Failed to delete message: {str(e)}")
            return False

    def _delete_from_cloudinary(self, image_url):
        """从Cloudinary删除图片"""
        try:
            public_id = self._extract_public_id(image_url)
            if public_id:
                destroy(public_id)
                logger.info(f"Successfully deleted image from Cloudinary: {public_id}")
        except Exception as e:
            logger.error(f"Failed to delete image from Cloudinary: {e}")

    def _extract_public_id(self, image_url):
        """从Cloudinary图片URL中提取public_id"""
        try:
            url_parts = image_url.split('/')
            upload_index = url_parts.index('upload')
            public_id_with_version = url_parts[upload_index + 1]
            public_id = public_id_with_version.split('/')[-1].split('.')[0]
            return public_id
        except Exception as e:
            logger.error(f"Failed to extract public_id from URL: {e}")
            return None
