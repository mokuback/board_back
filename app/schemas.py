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
        ofrom_attributes = True

class Message(MessageBase):
    id: int
    created_at: datetime
    user_id: int
    display_name: str
    is_admin: bool 

    class Config:
        from_attributes  = True

# 工作分类相关模式
class TaskCategoryBase(BaseModel):
    category_name: str
    content: str

class TaskCategoryCreate(TaskCategoryBase):
    pass

class TaskCategory(TaskCategoryBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 类别项目相关模式
class TaskItemBase(BaseModel):
    item_name: str
    content: str
    item_at: Optional[datetime] = None

class TaskItemCreate(TaskItemBase):
    category_id: int

class TaskItem(TaskItemBase):
    id: int
    category_id: int
    user_id: int
    item_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# 项目进度相关模式
class TaskProgressBase(BaseModel):
    progress_name: str
    content: str
    progress_at: Optional[datetime] = None

class TaskProgressCreate(TaskProgressBase):
    item_id: int

class TaskProgress(TaskProgressBase):
    id: int
    item_id: int
    user_id: int
    progress_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True        