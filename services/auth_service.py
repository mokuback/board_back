# board_back/services/auth_service.py
from services.base_service import BaseService
from utils.logger import logger
from werkzeug.security import check_password_hash
from utils.config import Config
from models import User
import jwt
from datetime import datetime, timedelta
import uuid

class AuthService(BaseService):
    def authenticate(self, username: str, password: str):
        """验证用户密码并返回JWT令牌"""
        try:
            with next(self.db.get_db()) as db:
                # 查询用户
                user = db.query(User).filter(User.username == username).first()
                
                # 验证用户存在且密码正确
                if user and check_password_hash(user.password_hash, password):
                    # 生成JWT令牌
                    token = self._generate_token(user.id)
                    return {
                        'success': True,
                        'token': token,
                        'user': {
                            'id': user.id,
                            'username': user.username
                        }
                    }
                
                return {
                    'success': False,
                    'message': '用户名或密码错误'
                }
        except Exception as e:
            logger.error(f"认证失败: {str(e)}")
            return {
                'success': False,
                'message': '认证过程中发生错误'
            }
    
    def _generate_token(self, user_id: str) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24),  # 令牌有效期24小时
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token: str):
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的令牌")
            return None
