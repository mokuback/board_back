# routes/messages.py
from flask import Blueprint, request, jsonify
from services.message_service import MessageService
from utils.auth import token_required

messages_bp = Blueprint('messages', __name__)
message_service = MessageService()

@messages_bp.route('/api/messages', methods=['GET'])
def get_messages():
    """获取所有留言"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 如果提供了分页参数，使用分页查询
        if page > 0 and per_page > 0:
            result = message_service.get_messages_with_pagination(page, per_page)
        else:
            # 否则获取所有留言
            messages = message_service.get_all_messages()
            result = {
                'items': messages,
                'total': len(messages),
                'pages': 1,
                'current_page': 1
            }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/api/messages', methods=['POST'])
@token_required
def add_message():
    """添加新留言"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'message': 'Content is required'
            }), 400
        
        content = data.get('content')
        image_url = data.get('image_url')
        user_id = getattr(request, 'user_id', None)
        
        message = message_service.add_message(content, image_url, user_id)
        if message:
            return jsonify({
                'success': True,
                'data': message
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add message'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/api/messages/<int:message_id>', methods=['DELETE'])
@token_required
def delete_message(message_id):
    """删除留言"""
    try:
        success = message_service.delete_message(message_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Message deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@messages_bp.route('/api/messages/user/<int:user_id>', methods=['GET'])
def get_messages_by_user(user_id):
    """获取指定用户的所有留言"""
    try:
        messages = message_service.get_messages_by_user(user_id)
        return jsonify({
            'success': True,
            'data': messages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
