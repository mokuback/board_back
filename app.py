from flask import Flask
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 数据库连接配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_rwfI5m8ihqZE@ep-flat-moon-adc7i78o-pooler.c-2.us-east-1.aws.neon.tech/board?sslmode=require&channel_binding=require')
engine = create_engine(DATABASE_URL)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/api/health')
def health_check():
    try:
        # 尝试连接数据库
        with engine.connect() as connection:
            return {
                "status": "healthy",
                "database": "connected"
            }
    except SQLAlchemyError as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == '__main__':
    app.run(debug=True)
