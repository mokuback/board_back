# board_back/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from utils.config import Config
from utils.database import Database
from routes.auth import auth_bp
from routes.messages import messages_bp
from utils.logger import logger

# 导入模型以确保它们被注册到 Base.metadata 中
from models import User, Message

def create_app():
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(messages_bp)
    
    # 初始化数据库
    db = Database()
    
    # 创建表（如果不存在）
    Base.metadata.create_all(db.engine)
    
    # 确保上传目录存在
    Config.ensure_upload_folder()
    
    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'API is running'
        })
    
    logger.info("Application initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
