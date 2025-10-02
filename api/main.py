from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime
import time
import asyncio
import requests
from jose.exceptions import ExpiredSignatureError, JWTError
from app.config import Config
from app.line_service import send_line_notification
from app import models, schemas, crud, auth
from app.database import SessionLocal, engine

app = FastAPI(
    title="Message Board API",
    description="A simple message board backend API",
    version="1.0.0"    
)

# allow_origins=["https://boardfront.vercel.app"],
# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

security = HTTPBearer()

def check_config():
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "LINE_MESSAGING_CHANNEL_ID",
        "LINE_MESSAGING_ACCESS_TOKEN", # LINE Messaging API
        "LINE_LOGIN_CHANNEL_ID",
        "LINE_LOGIN_CHANNEL_SECRET", # LINE Login (LIFF)
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    ]
    
    missing_vars = [var for var in required_vars if not getattr(Config, var, None)]

    if missing_vars:
        raise ValueError(f"缺少必要的環境變數： {', '.join(missing_vars)}")

def get_db_for_login(max_retries=3, delay=1):
    """用于登录的数据库连接，不需要token验证"""
    def _get_db():
        retries = 0
        db = None  # 初始化 db 变量
        while retries < max_retries:
            try:
                print(f"---------数据库连接 (尝试 {retries}/{max_retries})")
                db = SessionLocal()
                yield db
                return
            except Exception as e:
                # 如果是HTTPException，直接传播，不重试
                if isinstance(e, HTTPException):
                    raise
                # 其他异常才重试                
                retries += 1
                print(f"---------数据库连接失败 (尝试 {retries}/{max_retries}): {str(e)}")                
                if retries == max_retries:
                   raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="資料庫連接失敗",
                    )
                time.sleep(delay)
            finally:
                print(f"---------数据库關閉 (尝试 {retries}/{max_retries})")
                if db:
                    db.close()                
    return _get_db

def get_db_with_retry(max_retries=3, delay=1):
    def _get_db(credentials: HTTPAuthorizationCredentials = Depends(security)):
        # 验证 token
        try:
            token = credentials.credentials
            username = auth.verify_token(token)
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無法驗證憑證",
                headers={"WWW-Authenticate": "Bearer"},
            )        
        retries = 0
        db = None  # 初始化 db 变量
        while retries < max_retries:
            try:
                db = SessionLocal()
                yield db
                return
            except Exception as e:
                # 如果是HTTPException，直接传播，不重试
                if isinstance(e, HTTPException):
                    raise
                # 其他异常才重试                   
                retries += 1
                if retries == max_retries:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="資料庫連接失敗",
                    )
                time.sleep(delay)
            finally:
                if db:
                    db.close()                
    return _get_db

# board_back/app/main.py
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db_with_retry())):
    try:
        token = credentials.credentials
        username = auth.verify_token(token)
        user = crud.get_user_by_username(db, username=username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="沒有這個使用者",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無法驗證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="伺服器內部錯誤"
        )


@app.get("/")
def read_root():
    return {"message": "Welcome to the Message Board API"}

@app.post("/token")
async def login_for_access_token(
    form_data: dict, 
    db: Session = Depends(get_db_for_login())
):
    try:
        user = crud.get_user_by_username(db, username=form_data["username"])
        if not user or not auth.verify_password(form_data["password"], user.password_hash):
            # return {"ok": False, "detail": "錯誤的使用者名稱或密碼"}
            # print('---login_for_access_token--錯誤的使用者名稱或密碼-----')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="錯誤的使用者名稱或密碼",
                headers={"WWW-Authenticate": "Bearer"},
            )        
        
        # 创建登录记录
        crud.create_login_record(db, user.id)

        # 如果不是管理员，发送 LINE 通知
        if not user.is_admin:

            # 異步執行
            # asyncio.create_task(
            #     send_line_notification(
            #         user_id=Config.LINE_MESSAGING_ADMIN_ID,  # 假设 username 存储的是 LINE user id
            #         message="使用者登入訊息系統"
            #     )
            # ) 

            # 同步執行
            try:
                await send_line_notification(
                    user_id=Config.LINE_MESSAGING_ADMIN_ID,
                    message="使用者登入訊息系統"
                )
            except Exception as e:
                print(f"LINE 通知發送失敗: {str(e)}")
                # 不抛出异常，继续执行登录流程          

        # 更新 displayname(有時間時，修改此段挪到 crud)
        display_name = form_data.get("displayname")
        if display_name:
            # 检查是否已存在 displayname 记录
            existing_display_name = db.query(models.DisplayName).filter(
                models.DisplayName.user_id == user.id
            ).first()
            
            if existing_display_name:
                # 更新现有的 displayname
                existing_display_name.displayname = display_name
                existing_display_name.updated_at = func.now()
            else:
                # 创建新的 displayname 记录
                new_display_name = models.DisplayName(
                    user_id=user.id,
                    displayname=display_name
                )
                db.add(new_display_name)
            
            db.commit()


        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"ok": True, "access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin}
    except HTTPException as e:
    #     print("Error: ----------HTTPException--------------")     
        # 只處理HTTPException，讓它正常傳播
        raise e
    except Exception as e:
        # print("Error: ----------Exception--------------")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="伺服器內部錯誤",
        )

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db_for_login())):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="使用者名稱已經存在"
        )
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/messages/", response_model=list[schemas.Message])
def get_messages(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_with_retry())
):
    try:
        messages = db.query(models.Message).order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()

        # 为每条消息添加display_name和is_admin
        for message in messages:
            user = db.query(models.User).filter(
                models.User.id == message.user_id
            ).first()
            display_name = db.query(models.DisplayName).filter(
                models.DisplayName.user_id == message.user_id
            ).first()
            message.display_name = display_name.displayname if display_name else "Anonymous"
            message.is_admin = user.is_admin if user else False
        return messages
    except HTTPException as e:
        raise e
    except Exception as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取留言失敗"
        )

@app.post("/messages/")
async def create_message(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_with_retry())
):
    """
    创建消息，支持文本和图片上传
    """
    try:
        # 获取表单数据
        form = await request.form()
        content = form.get("content")
        file = form.get("file")

        # 创建消息对象
        message = schemas.MessageCreate(content=content)

        # 调用 crud.py 的 create_user_message 处理验证和上传
        result = await crud.create_user_message(
            db=db,
            message=message,
            user_id=current_user.id,
            file=file
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="留言新增失敗"
            )

        # 如果不是管理员，发送 LINE 通知
        if not current_user.is_admin:

            # 異步執行
            # asyncio.create_task(
            #     send_line_notification(
            #         user_id=Config.LINE_MESSAGING_ADMIN_ID,  # 假设 username 存储的是 LINE user id
            #         message="使用者登入訊息系統"
            #     )
            # ) 

            # 同步執行
            try:
                await send_line_notification(
                    user_id=Config.LINE_MESSAGING_ADMIN_ID,
                    message="使用者新增訊息"
                )
            except Exception as e:
                print(f"LINE 通知發送失敗: {str(e)}")
                # 不抛出异常，继续执行登录流程   

        return {
            "ok": True,
            "message": "留言新增成功",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db_with_retry()),
    current_user: models.User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="沒有刪除留言的權限"
        )
    
    message = crud.delete_message(db=db, message_id=message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="刪除留言失敗"
        )
    return {"ok": True, "message": "刪除留言成功"}

@app.put("/users/password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db_with_retry()),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print("=== Debug Info ===")
        print("Current user:", current_user.username)
        
        # 获取并解码密码
        data = await request.json()
        import base64
        old_password = base64.b64decode(data.get("old_password")).decode()
        new_password = base64.b64decode(data.get("new_password")).decode()
        
        # 验证输入
        if not old_password or not new_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="缺少必要參數"
            )
        
        # 在当前会话中重新获取用户对象
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="使用者不存在"
            )        
            
        # 验证旧密码
        if not auth.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密碼錯誤"
            )
        
        # 生成新密码哈希
        new_password_hash = auth.get_password_hash(new_password)
        print("New password hash generated")
        
        # 更新密码
        user.password_hash = new_password_hash
        db.commit()
        db.refresh(user)  # 刷新实例以获取更新后的数据
        
        return {"ok": True, "message": "密碼修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating password: {str(e)}")
        db.rollback()  # 发生错误时回滚
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密碼更新失敗"
        )
    
@app.get("/admin/login-records/", response_model=list[schemas.LoginRecord])
def get_all_login_records(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_with_retry())
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅限管理員訪問"
        )
    
    try:
        records = db.query(models.LoginRecord).order_by(
            models.LoginRecord.login_datetime.desc()
        ).all()

        for record in records:
            display_name = db.query(models.DisplayName).filter(
                models.DisplayName.user_id == record.user_id
            ).first()
            record.display_name = display_name.displayname if display_name else "Anonymous"
            
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取登入記錄失敗"
        )

@app.get("/tasks/all", response_model=dict)
def get_all_task_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_with_retry())
):
    """
    获取所有任务相关数据，包括分类、项目和进度
    需要有效的用户token
    """
    try:
        print(f"=== categories ===")
        # 获取所有分类
        categories = db.query(models.TaskCategory).filter(
            models.TaskCategory.user_id == current_user.id
        ).all()
        print(f"Found {len(categories)} categories")
        
        print(f"=== items ===")
        # 获取所有项目
        try:
            items = db.query(models.TaskItem).filter(
                models.TaskItem.user_id == current_user.id
            ).all()
            print(f"Found {len(items)} items")
        except Exception as item_error:
            print(f"Error fetching items: {str(item_error)}")
            # 尝试不带用户过滤的查询
            items = db.query(models.TaskItem).all()
            print(f"Found {len(items)} items without user filter")
        
        print(f"=== progresses ===")
        # 获取所有进度
        try:
            progresses = db.query(models.TaskProgress).filter(
                models.TaskProgress.user_id == current_user.id
            ).all()
            print(f"Found {len(progresses)} progresses")
        except Exception as progress_error:
            print(f"Error fetching progresses: {str(progress_error)}")
            # 尝试不带用户过滤的查询
            progresses = db.query(models.TaskProgress).all()
            print(f"Found {len(progresses)} progresses without user filter")
        
        # 将数据转换为字典格式，避免序列化问题
        def model_to_dict(model):
            if hasattr(model, '__table__'):
                return {c.name: getattr(model, c.name) for c in model.__table__.columns}
            return model
        
        # 转换数据
        categories_data = [model_to_dict(category) for category in categories]
        items_data = [model_to_dict(item) for item in items]
        progresses_data = [model_to_dict(progress) for progress in progresses]
        
        # 返回组织好的数据
        return {
            "categories": categories_data,
            "items": items_data,
            "progresses": progresses_data
        }
    except Exception as e:
        print(f'General error in get_all_task_data: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取任務數據失敗: {str(e)}"
        )



@app.get("/api/health")
def health_check():
    health_status = {
        "status": "健康",
        "components": {
            "config": {"status": "正常"},
            "database": {"status": "未檢查"},
            "api": {"status": "正常"}
        }
    }

    # 检查配置
    try:
        check_config()
    except ValueError as e:
        health_status["status"] = "不健康"
        health_status["components"]["config"] = {
            "status": "錯誤",
            "error": str(e)
        }
            
    # 检查数据库连接
    try:
        with engine.connect() as connection:
            health_status["components"]["database"] = {
                "status": "已連接"
            }
    except Exception as e:
        health_status["status"] = "不健康"
        health_status["components"]["database"] = {
            "status": "已斷開",
            "error": str(e)
        }

    return health_status

# Vercel 需要的處理程序
# def handler(request):
#     return app(request.scope, receive=request.receive, send=request.send)
