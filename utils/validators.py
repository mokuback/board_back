# utils/validators.py
from pydantic import BaseModel, validator
from typing import Optional

class MessageModel(BaseModel):
    content: str
    image_url: Optional[str] = None
    user_id: Optional[int] = None

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 500:
            raise ValueError('Content cannot exceed 500 characters')
        return v.strip()

class Validators:
    """验证工具类，包含各种验证方法"""
    
    @staticmethod
    def validate_message(message_data):
        """验证消息数据"""
        try:
            return MessageModel(**message_data)
        except Exception as e:
            raise ValueError(f"Invalid message data: {str(e)}")
