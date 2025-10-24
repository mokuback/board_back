from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from datetime import datetime, time


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
        from_attributes = True


# 工作分类相关模式
class TaskCategoryBase(BaseModel):
    category_name: str
    content: str


class TaskCategoryCreate(BaseModel):
    """创建任务分类的数据模型"""
    category_name: str
    content: str = ""

    class Config:
        from_attributes = True


class TaskCategory(BaseModel):
    """任务分类的响应模型"""
    id: int
    user_id: int
    category_name: str
    content: str
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
    status: int = 0


class TaskProgressCreate(TaskProgressBase):
    item_id: int


class TaskProgress(TaskProgressBase):
    id: int
    item_id: int
    user_id: int
    progress_at: datetime
    created_at: datetime
    status: int

    class Config:
        from_attributes = True


class TaskCategoryUpdate(BaseModel):
    """更新任务分类的数据模型"""
    category_name: str
    content: str = ""

    class Config:
        from_attributes = True


class TaskItemUpdate(BaseModel):
    """更新任务项目的数据模型"""
    item_name: str
    content: str = ""
    item_at: Optional[datetime] = None


class TaskProgressUpdate(BaseModel):
    """更新任务进度的数据模型"""
    progress_name: str
    content: str = ""
    progress_at: Optional[datetime] = None
    status: Optional[int] = None


class TaskNotifyBase(BaseModel):
    category_id: int
    item_id: int
    progress_id: int
    start_at: datetime
    stop_at: datetime
    run_mode: int
    run_code: int
    time_at: Optional[time] = None
    week_at: Optional[int] = None
    last_executed: Optional[datetime] = None


class TaskNotifyCreate(TaskNotifyBase):
    pass


class TaskNotify(TaskNotifyBase):
    id: int
    user_id: int
    created_at: datetime
    last_executed: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskNotifyUpdate(BaseModel):
    """更新任务通知的数据模型"""
    start_at: Optional[datetime] = None
    stop_at: Optional[datetime] = None
    run_mode: Optional[int] = None
    run_code: Optional[int] = None
    time_at: Optional[str] = None
    week_at: Optional[int] = None
    last_executed: Optional[datetime] = None


class TaskNotify(TaskNotifyBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
