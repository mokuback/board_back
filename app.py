import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text, inspect
from utils.config import Config
from utils.database import Database
from routes.auth import auth_bp
from routes.messages import messages_bp
from utils.logger import logger
from models import Base

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
    
    # 添加数据库连接检查
    try:
        with db.engine.connect() as conn:
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None
    
    # 创建表（如果不存在）
    Base.metadata.create_all(db.engine)
    
    # 确保上传目录存在
    Config.ensure_upload_folder()
    
    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        try:
            # 测试数据库连接
            db = Database()
            with db.engine.connect() as conn:
                # 执行简单查询测试连接
                conn.execute(text("SELECT 1"))
                
                # 如果是本地环境，获取所有表名
                tables = []
                if Config.DEBUG:  # 本地环境判断
                    inspector = inspect(db.engine)
                    tables = inspector.get_table_names()
                    
                response = {
                    'status': 'healthy',
                    'message': 'API is running',
                    'database': 'connected'
                }
                
                if tables:
                    response['tables'] = tables
                    
                return jsonify(response)
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error': str(e)
            }), 500
        
    # 在健康检查端点之后添加
    @app.route('/api/test')
    def test_server():
        """测试 web 服务器是否正常运行"""
        return jsonify({
            'status': 'ok',
            'message': 'Web server is running'
        })        

    logger.info("Application initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    if app:
        app.run(host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to create application")
