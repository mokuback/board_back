# utils/auth.py
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
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
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    @staticmethod
    def token_required(f):
        """JWT令牌验证装饰器"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({
                    'success': False,
                    'message': '缺少认证令牌'
                }), 401
            
            try:
                token = token.split(' ')[1]  # 去掉 'Bearer ' 前缀
                if not AuthUtils.verify_token(token):
                    return jsonify({
                        'success': False,
                        'message': '无效的认证令牌'
                    }), 401
            except:
                return jsonify({
                    'success': False,
                    'message': '令牌格式错误'
                }), 401
            
            return f(*args, **kwargs)
        return decorated

# 导出需要的组件
token_required = AuthUtils.token_required
