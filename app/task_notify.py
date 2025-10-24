import asyncio
from datetime import datetime, time, timezone, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from . import models
from .line_service import send_line_notification
from app.config import Config
import re
import pytz
from .connections import connections


class TaskNotify:
    CHECK_INTERVAL = 60  # 检查间隔(秒)，前端在run_mode = 0 時，限制要比當前時間晚十分鐘以上
    TIMEZONE = timezone.utc  # 时区常量
    LINE_NOTIFY = 'line_notify'

    def local_time_to_utc(self, local_time: time) -> datetime:
        """
        将当地时间转换为UTC时间
        参数:
            local_time: 本地时间对象
        返回:
            datetime: 对应的UTC日期时间对象
        """
        try:
            local_tz = pytz.timezone(Config.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            print(f"未知的时区: {Config.TIMEZONE}，使用 Asia/Taipei")
            local_tz = pytz.timezone('Asia/Taipei')

        # 获取当前本地日期
        now = datetime.now(local_tz)

        # 组合本地日期和传入的时间
        local_datetime = datetime.combine(now.date(), local_time)

        # 设置时区
        local_datetime = local_tz.localize(local_datetime)

        # 转换为UTC时间
        utc_datetime = local_datetime.astimezone(pytz.UTC)

        return utc_datetime

    def get_local_time(self):
        """获取当地时间和星期值"""
        try:
            local_tz = pytz.timezone(Config.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            print(f"未知的时区: {Config.TIMEZONE}，使用 Asia/Taipei")
            local_tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(local_tz)
        return now.time(), now.weekday() + 1  # weekday()返回0-6，加1转换为1-7

    @staticmethod
    def validate_line_id(line_id: str) -> bool:
        """
        验证LINE ID格式是否正确
        参数:
            line_id: 需要验证的LINE ID字符串
        返回:
            bool: 验证结果，如果格式正确返回true，否则返回false
        """
        # LINE ID 格式验证规则：
        # 1. 必须以 'U' 开头
        # 2. 总长度为 33 个字符
        # 3. 只包含字母和数字
        return bool(re.match(r'^U[a-zA-Z0-9]{32}$', line_id))

    def __init__(self, db: Session):
        """
        初始化TaskNotify类实例
        参数:
            db: 数据库会话对象
        """
        self.db = db
        self.notifies: List[Dict] = []  # 存储通知记录的列表
        self._running = False  # 运行状态标志

    async def load_notifies(self):
        """加载符合条件的通知记录"""
        print("\n=== 开始加载通知 ===")
        now = datetime.now(self.TIMEZONE)
        print(f"当前时间: {now}")

        # 提前10分钟和延后10分钟的时间点
        early_time = now - timedelta(minutes=10)
        late_time = now + timedelta(minutes=10)

        # 查询通知记录并关联用户表
        notifies = self.db.query(models.TaskNotify, models.User.username).join(
            models.User, models.TaskNotify.user_id == models.User.id).filter(
                # 单次执行模式：加载开始时间在10分钟内的通知(單次已有執行過通知的不加载)
                (models.TaskNotify.run_mode == 0)
                & (models.TaskNotify.start_at > early_time)
                & (models.TaskNotify.last_executed.is_(None))
                |
                # 重复执行模式：加载时间范围扩大10分钟的通知
                (models.TaskNotify.run_mode.in_([1, 2]))
                & (models.TaskNotify.start_at <= late_time)
                & (models.TaskNotify.stop_at > early_time)).all()

        # 转换为字典格式并添加username字段
        self.notifies = []
        for notify, username in notifies:
            notify_dict = notify.__dict__.copy()
            notify_dict['username'] = username
            self.notifies.append(notify_dict)

    async def check_notifies(self):
        """检查并执行通知"""
        now = datetime.now(self.TIMEZONE)
        # current_time = now.time()
        # current_week = now.weekday() + 1  # 转换为 1-7 (Monday to Sunday)
        current_time, current_week = self.get_local_time()

        print(
            f"\n=== 开始检查通知 ({now}) current_time ({current_time} current_week {current_week}) ==="
        )
        print(f"当前通知数量: {len(self.notifies)}")

        for notify in self.notifies[:]:  # 创建副本以便安全删除
            try:
                utc_time_at = self.local_time_to_utc(notify['time_at'])
                print(f"\n检查通知 ID: {notify['id']}")
                # print(f"通知详情: {notify}")

                # 检查执行条件
                should_execute = False

                # 单次执行模式
                if notify['run_mode'] == 0:
                    print(f"通知 ID: {notify['id']} run_mode 为 0")
                    print(f"当前时间: {now}")
                    print(f"开始时间: {notify['start_at']}")
                    print(f"时间比较: {now >= notify['start_at']}")

                    # 只检查开始时间
                    if now >= notify['start_at']:
                        print(f"通知 ID: {notify['id']} 时间已到，准备执行")
                        should_execute = True
                    else:
                        print(f"通知 ID: {notify['id']} 时间未到")
                        print(f"通知 ID: {notify['id']} 跳过后续检查")
                        continue

                # 检查是否超过停止时间
                elif now >= notify['stop_at']:
                    print(f"通知 ID: {notify['id']} run_mode 为 1 或 2")
                    print(f"通知 ID: {notify['id']} 已超过停止时间，移除")
                    self.notifies.remove(notify)
                    continue
                elif notify['run_mode'] == 1:
                    print(f"通知 ID: {notify['id']} run_mode 为 1")
                    print(f"通知 ID: {notify['id']} 未过停止时间，继续检查")
                    print(f"当前时间: {now}")
                    print(f"开始时间: {notify['start_at']}")
                    print(f"时间比较: {now >= notify['start_at']}")
                    print(f"執行時間: {notify['time_at']}")
                    if (now >= notify['start_at']
                            and utc_time_at >= notify['start_at']
                            and current_time >= notify['time_at'] and
                        (not notify['last_executed']
                         or now.date() > notify['last_executed'].date())):
                        print(f"通知 ID: {notify['id']} 时间已到，准备执行")
                        should_execute = True
                elif notify['run_mode'] == 2:
                    print(f"通知 ID: {notify['id']} run_mode 为 2")
                    print(f"通知 ID: {notify['id']} 未过停止时间，继续检查")
                    print(f"当前星期: {current_week}")
                    print(f"開始星期: {notify['week_at']}")
                    print(
                        f"星期比较: {current_week in [int(d) for d in str(notify['week_at'])]}"
                    )
                    print(f"当前时间: {now}")
                    print(f"开始时间: {notify['start_at']}")
                    print(f"时间比较: {now >= notify['start_at']}")
                    print(f"執行時間: {notify['time_at']}")
                    if (now >= notify['start_at']
                            and utc_time_at >= notify['start_at']
                            and current_week in
                        [int(d) for d in str(notify['week_at'])
                         ]  # and str(current_week) in str(notify['week_at'])
                            and current_time >= notify['time_at'] and
                        (not notify['last_executed']
                         or now.date() > notify['last_executed'].date())):
                        should_execute = True

                print(f"当前通知数量: {len(self.notifies)}")
                if should_execute:
                    print(f"通知 ID: {notify['id']} 符合执行条件，执行通知")
                    await self.execute_notify(notify, now)
                    if notify['run_mode'] == 0:
                        print(f"通知 {notify['id']} 已执行，移除")
                        self.notifies.remove(notify)
                print(f"当前通知数量: {len(self.notifies)}")
            except Exception as e:
                print(f"处理通知 {notify['id']} 时出错: {str(e)}")

    async def execute_notify(self, notify: Dict, current_time: datetime):
        """执行指定的通知函数"""
        # 验证 LINE ID 格式
        if not self.validate_line_id(notify['username']):
            print(f"无效的 LINE ID 格式: {notify['username']}")
            return

        # 先验证相关对象是否存在
        details = self.get_progress_details(notify['category_id'],
                                            notify['item_id'],
                                            notify['progress_id'])

        if not details:
            return

        print(
            f"run_code = {notify['run_code']} 发送 LINE 通知给用户 ID: {notify['user_id']}"
        )
        await send_line_notification(notify['username'],
                                     details['progress_content'])
        # 更新指定通知记录的最后执行时间
        self.update_last_executed(notify['id'], current_time)

        # 只通知特定用户

        # 只向该用户的连接发送通知
        # 构造消息数据
        message_data = {
            "id": notify['id'],
            "category_id": notify['category_id'],
            "item_id": notify['item_id'],
            "progress_id": notify['progress_id'],
            "last_executed": current_time.isoformat(),
            # "category_name": details['category_name'],
            # "item_name": details['item_name'],
            # "progress_name": details['progress_name']
            # "progress_content": details['progress_content']
        }
        # 发送给用户的数据
        data = {"message": message_data, "type": self.LINE_NOTIFY}
        print(f"通知 ID: {notify['id']} 通知内容: {data}")
        await self.send_to_user(notify['user_id'], data)

    async def send_to_user(self, user_id: int, data: Dict):
        """
        向特定用户的所有连接队列发送数据
        
        参数:
            user_id: 用户ID
            data: 要发送的数据字典
        """

        # 检查用户ID是否存在于connections字典中
        if user_id in connections:  # 验证用户是否有活跃连接
            # 遍历该用户的所有连接队列
            # for queue in connections[user_id]:  # 对每个用户连接进行处理
            for device_id, queue in connections[user_id].items():
                print(f"向用户 ID: {user_id} (设备ID: {device_id})")
                # 将数据异步放入队列
                await queue.put(data)  # 使用异步方式将数据放入队列

    async def start(self):
        """启动通知检查循环"""
        self._running = True
        await self.load_notifies()
        while self._running:
            await self.check_notifies()
            await asyncio.sleep(self.CHECK_INTERVAL)

    def stop(self):
        """停止通知检查循环"""
        self._running = False

    def add_notify(self, notify_data: Dict):
        """添加新的通知记录到列表中（不保存到数据库）"""
        # 生成新的ID
        new_id = max([n['id'] for n in self.notifies], default=0) + 1
        # 创建新通知字典
        new_notify = {'id': new_id, **notify_data}
        # 添加到列表
        self.notifies.append(new_notify)
        return new_notify

    def remove_notify(self, notify_id: int):
        """从通知列表中移除记录（不删除数据库记录）"""
        for notify in self.notifies[:]:  # 创建副本以便安全删除
            if notify['id'] == notify_id:
                self.notifies.remove(notify)
                return notify
        return None

    async def refresh_notifies(self):
        """手动刷新通知列表"""
        try:
            # 确保回滚任何未完成的事务
            self.db.rollback()
            await self.load_notifies()
        except Exception as e:
            print(f"刷新通知列表失败: {str(e)}")
            self.db.rollback()
            raise

    def get_progress_details(self, category_id: int, item_id: int,
                             progress_id: int):
        """获取分类、项目和进度的详细信息"""
        try:
            # 查询分类
            category = self.db.query(models.TaskCategory).filter(
                models.TaskCategory.id == category_id).first()

            # 查询项目
            item = self.db.query(
                models.TaskItem).filter(models.TaskItem.id == item_id).first()

            # 查询进度
            progress = self.db.query(models.TaskProgress).filter(
                models.TaskProgress.id == progress_id).first()

            # 如果任何一个ID不存在，返回None
            if not category or not item or not progress:
                return None

            # 返回所需信息
            return {
                "category_name": category.category_name,
                "item_name": item.item_name,
                "progress_name": progress.progress_name,
                "progress_content": progress.content
            }
        except Exception as e:
            print(f"Error getting progress details: {str(e)}")
            return None

    def update_last_executed(self,
                             notify_id: int,
                             current_time: datetime = None):
        """
        更新指定通知记录的最后执行时间
        参数:
            notify_id: 要更新的通知记录ID
            current_time: 调用者提供的当前时间，如果为None则将last_executed设为null
        返回:
            bool: 更新是否成功
        """
        try:
            # 更新数据库记录
            updated = self.db.query(models.TaskNotify).filter(
                models.TaskNotify.id == notify_id).update(
                    {'last_executed': current_time if current_time else None})

            # 提交事务
            self.db.commit()

            # 同时更新内存中的记录
            for notify in self.notifies:
                if notify['id'] == notify_id:
                    notify[
                        'last_executed'] = current_time if current_time else None
                    break

            return bool(updated)
        except Exception as e:
            print(f"更新最后执行时间失败: {str(e)}")
            self.db.rollback()
            return False
