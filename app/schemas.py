from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    image_url: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class LoginRecord(BaseModel):
    id: int
    user_id: int
    login_datetime: datetime
    display_name: str
    
    class Config:
        orm_mode = True

class Message(MessageBase):
    id: int
    created_at: datetime
    user_id: int
    display_name: str
    is_admin: bool 

    class Config:
        from_attributes  = True
