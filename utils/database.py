# board_back/utils/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from .config import Config
from .logger import logger

load_dotenv()

# 从 models 导入 Base，而不是在这里创建新的 Base
from models import Base

class Database:
    def __init__(self):
        self._engine = create_engine(
            Config.DATABASE_URL,
            **Config.SQLALCHEMY_ENGINE_OPTIONS
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        
    @property
    def engine(self):
        return self._engine
        
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
        
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self._engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
