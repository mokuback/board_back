from abc import ABC
from utils.database import Database
from utils.logger import logger

class BaseService(ABC):
    def __init__(self):
        self.db = Database()
    
    def _execute_with_session(self, operation, *args, **kwargs):
        """通用数据库操作执行方法"""
        session = self.db.get_session()
        try:
            result = operation(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise e
        finally:
            session.close()
