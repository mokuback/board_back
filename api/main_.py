# api/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def test():
    return {"status": "ok"}