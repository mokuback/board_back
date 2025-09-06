from werkzeug.security import check_password_hash
from models import User
from utils.logger import logger
from datetime import datetime, timezone, timedelta
import jwt
from utils.config import Config
from .base_service import BaseService

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
                            'username': user.username,
                            'is_admin': user.is_admin
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

    def _generate_token(self, user_id: int) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

    def verify_token(self, token: str):
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
