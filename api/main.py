# api/main.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def test():
    return {"status": "ok"}

# Vercel 需要的處理程序
def handler(request):
    return app(request.scope, receive=request.receive, send=request.send)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)