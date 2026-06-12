import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from bot import main as start_bot

app = FastAPI()

@app.get("/")
async def read_index():
    with open("webapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

async def serve_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    server = uvicorn.Server(config)
    await server.serve()

async def main_async():
    # FastAPI va Botni birgalikda ishga tushirish (agar Webhook ishlatmasak)
    # Hozircha oddiygina ikkalasini run qilamiz. 
    # Lekin bot polling da ishlagani uchun bloklanib qolishi mumkin,
    # shuning uchun botni asyncio task sifatida ishga tushiramiz.
    
    # Aslida, production da Webhook ishlatiladi yoki 2 ta alohida process qilinadi.
    pass

if __name__ == "__main__":
    # Render.com kabi platformalarda web server (FastAPI) ishga tushishi kerak.
    # Lekin bot ham ishlashi kerak. Shuning uchun hozircha test uchun faqat botni o'zini yurgizamiz
    # WebApp URL uchun Render ga deploy qilinganda fastapi ishlashi kerak.
    
    # Agar bu fayl chaqirilsa fastapi ni yurgizamiz.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
