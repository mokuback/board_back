from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="user")
    display_name = relationship("DisplayName", back_populates="user", uselist=False)
    login_records = relationship("LoginRecord", back_populates="user")    
    task_categories = relationship("TaskCategory", back_populates="user")
    task_items = relationship("TaskItem", back_populates="user")
    task_progresses = relationship("TaskProgress", back_populates="user")    

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="messages")

class DisplayName(Base):
    __tablename__ = "displaynames"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    displayname = Column(String(100), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="display_name")

class LoginRecord(Base):
    __tablename__ = "login_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    login_datetime = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="login_records")

# 工作分类模型
class TaskCategory(Base):
    __tablename__ = "task_categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 建立与用户的关系
    user = relationship("User", back_populates="task_categories")
    # 建立与项目的关系
    items = relationship("TaskItem", back_populates="category", cascade="all, delete-orphan")

# 工作分类-项目模型
class TaskItem(Base):
    __tablename__ = "task_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("task_categories.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    item_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    # 建立与用户的关系
    user = relationship("User", back_populates="task_items")    
    # 建立与分类的关系
    category = relationship("TaskCategory", back_populates="items")
    # 建立与进度的关系
    progresses = relationship("TaskProgress", back_populates="item", cascade="all, delete-orphan")

# 工作分类-项目-进度模型
class TaskProgress(Base):
    __tablename__ = "task_progresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("task_items.id", ondelete="CASCADE"), nullable=False)
    progress_name = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    progress_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Integer, nullable=False, server_default='0')
    
    # 建立与用户的关系
    user = relationship("User", back_populates="task_progresses")    
    # 建立与项目的关系
    item = relationship("TaskItem", back_populates="progresses")