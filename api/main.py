# api/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def test():
    return {"status": "ok"}

# Vercel 需要的處理程序
def handler(request):
    return app(request.scope, receive=request.receive, send=request.send)
