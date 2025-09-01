# utils/auth.py
import jwt
from datetime import datetime, timedelta, timezone
from .config import Config

class AuthUtils:
    """认证工具类，包含认证相关的方法"""
    
    @staticmethod
    def generate_token():
        """生成JWT令牌"""
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """验证JWT令牌"""
        try:
            jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            return True
        except:
            return False
