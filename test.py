# test.py
from app.main import handler

# 模擬 HTTP GET 請求
event = {
    "httpMethod": "GET",
    "path": "/",
    "headers": {},
    "queryStringParameters": {},
    "body": None,
    "isBase64Encoded": False
}
context = {}
response = handler(event, context)
print(response)