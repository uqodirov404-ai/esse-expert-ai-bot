import asyncio
import os
import threading
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from telegram.ext import Application
from bot import main as start_bot

app = FastAPI()

@app.get("/")
async def read_index():
    with open("webapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

def run_bot_thread():
    # Telegram botni alohida threadda yurgizish
    import bot
    bot.main()

if __name__ == "__main__":
    # Botni ishga tushirish (Background thread)
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()
    
    # Web serverni ishga tushirish (Main thread)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
