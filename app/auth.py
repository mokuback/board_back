"""
JWT认证和密码加密相关功能模块
包含密码哈希验证、JWT令牌创建和验证等功能
"""
from datetime import datetime, timedelta, timezone  # 导入可选类型提示  # 导入日期时间处理相关模块
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import Config

# 从环境变量中获取密钥
SECRET_KEY = Config.SECRET_KEY
# 设置JWT加密算法
ALGORITHM = "HS256"
# 设置访问令牌过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# 设置访问令牌过期时间（秒）
# ACCESS_TOKEN_EXPIRE_SECONDS = 60

# 创建密码加密上下文，使用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Could not validate credentials")
        return username
    except JWTError as e:
        # 不在这里处理过期错误，让调用者处理
        raise e
