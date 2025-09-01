# board_back/routes/__init__.py
from .auth import auth_bp
from .messages import messages_bp

__all__ = ['auth_bp', 'messages_bp']
