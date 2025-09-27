import asyncio
import httpx
from fastapi import HTTPException
from .config import Config


async def send_line_notification(user_id: str, message: str):
    # print('===send_line_notification===')
    # return
    """
    异步发送 LINE 通知
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {Config.LINE_MESSAGING_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code != 200:
                print(f"LINE 通知發送失敗: {response.text}")
    except Exception as e:
        print(f"發送 LINE 通知時發生錯誤: {str(e)}")
