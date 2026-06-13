import os
import aiofiles
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import asyncio
import threading
from config import BOT_TOKEN

from ai_engine import check_essay_text, check_essay_image
import bot

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def keep_alive():
    while True:
        try:
            requests.get("https://esse-expert-ai-bot.onrender.com/")
        except:
            pass
        await asyncio.sleep(840) # 14 mins

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

@app.get("/")
async def read_index():
    with open("webapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/upload")
async def upload_essay(
    user_id: int = Form(...),
    criteria: str = Form(...),
    topic: str = Form(""),
    text: str = Form(""),
    file: UploadFile = File(None)
):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": user_id, "text": "⏳ Essengiz qabul qilindi. AI uni tekshirmoqda, kuting..."}
        )

        async def process_and_send():
            result = ""
            try:
                if file and file.filename:
                    file_location = f"temp_{user_id}_{file.filename}"
                    async with aiofiles.open(file_location, 'wb') as out_file:
                        content = await file.read()
                        await out_file.write(content)
                    
                    result = await check_essay_image(file_location, criteria, topic)
                    os.remove(file_location)
                elif text:
                    result = await check_essay_text(text, criteria, topic)
                else:
                    result = "⚠️ Iltimos, esse matnini yozing yoki rasm yuklang!"
            except Exception as e:
                result = f"Xatolik yuz berdi: {str(e)}"
            
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": result, "parse_mode": "Markdown"}
            )
            
        asyncio.create_task(process_and_send())
        
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

def run_telegram_bot():
    bot.main()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
