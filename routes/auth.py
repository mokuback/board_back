from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
import jwt
from services.auth_service import AuthService
from utils.config import Config

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'success': False,
            'message': '用户名和密码不能为空'
        }), 400

    username = data['username']
    password = data['password']
    
    # 使用AuthService进行认证
    auth_result = auth_service.authenticate(username, password)
    
    if auth_result['success']:
        return jsonify({
            'success': True,
            'token': auth_result['token'],
            'user': auth_result['user'],
            'message': '登录成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': auth_result['message']
        }), 401
