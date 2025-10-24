import asyncio
from typing import Dict, List

# SSE 连接池，格式: {user_id: {device_id: queue}}
connections: Dict[int, Dict[str, asyncio.Queue]] = {}
