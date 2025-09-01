# test/test_db_connection.py
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# 添加父目录到路径，以便导入utils模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Base
from models.message import Message
from models import User

load_dotenv()

def test_connection():
    """测试数据库连接"""
    try:
        # 使用SQLAlchemy引擎连接
        engine = create_engine(os.getenv('DATABASE_URL'))
        
        # 执行简单查询
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            db_version = result.fetchone()
            
        print(f"成功连接到 PostgreSQL 数据库！")
        print(f"PostgreSQL 版本: {db_version[0]}")
        return True
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return False

def check_tables():
    """检查表是否存在"""
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        inspector = inspect(engine)
        
        # 获取所有表名
        tables = inspector.get_table_names()
        
        print(f"数据库中的表: {', '.join(tables)}")
        
        # 检查必要的表是否存在
        required_tables = ['users', 'messages']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"缺少表: {', '.join(missing_tables)}")
            return False
        else:
            print("所有必要的表都存在")
            return True
    except Exception as e:
        print(f"检查表失败: {e}")
        return False

def show_table_data(table_name, limit=10):
    """显示表数据"""
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        
        with engine.connect() as conn:
            # 检查表是否存在
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                print(f"表 '{table_name}' 不存在")
                return
                
            # 获取表数据
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
            rows = result.fetchall()
            
            # 获取列名
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            print(f"\n表 '{table_name}' 的数据 (最多 {limit} 条):")
            print("-" * 50)
            print("| " + " | ".join(columns) + " |")
            print("-" * 50)
            
            for row in rows:
                print("| " + " | ".join(str(cell) for cell in row) + " |")
                
            print(f"\n共显示 {len(rows)} 条记录")
    except Exception as e:
        print(f"获取表数据失败: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 有参数，显示表数据
        table_name = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_table_data(table_name, limit)
    else:
        # 没有参数，测试连接并检查表
        if test_connection():
            check_tables()
