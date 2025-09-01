from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
import jwt
from services.auth_service import AuthService
from utils.auth import token_required
from utils.config import Config

# 在实际应用中，这个密钥应该保存在环境变量中
SECRET_KEY = "your-secret-key"

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({
            'success': False,
            'message': '密码不能为空'
        }), 400
    password = data['password']
    if auth_service.authenticate(password):
        # 生成JWT令牌
        token = jwt.encode({
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            'iat': datetime.now(timezone.utc)
        }, Config.SECRET_KEY, algorithm="HS256")  # 使用 Config.SECRET_KEY

        
        return jsonify({
            'success': True,
            'token': token,
            'message': '登录成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '密码错误'
        }), 401
