import os
import aiofiles
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import asyncio
from config import BOT_TOKEN

# Async function import qilinadi
from ai_engine import check_essay_text, check_essay_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_index():
    with open("webapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

async def background_send_message(user_id, result):
    # Telegram Bot API ga to'g'ridan-to'g'ri so'rov jo'natish
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": result,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.post("/upload")
async def upload_essay(
    user_id: int = Form(...),
    criteria: str = Form(...),
    topic: str = Form(""),
    text: str = Form(""),
    file: UploadFile = File(None)
):
    try:
        # Xabarni qabul qilganini bildirish
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": user_id, "text": "⏳ Essengiz qabul qilindi. AI uni tekshirmoqda, kuting..."}
        )

        async def process_and_send():
            result = ""
            try:
                if file and file.filename:
                    # Rasmni vaqtincha saqlash
                    file_location = f"temp_{user_id}_{file.filename}"
                    async with aiofiles.open(file_location, 'wb') as out_file:
                        content = await file.read()
                        await out_file.write(content)
                    
                    # Rasmni AI ga tekshirish
                    result = await check_essay_image(file_location, criteria, topic)
                    
                    # Rasmni o'chirish
                    os.remove(file_location)
                elif text:
                    # Matnni AI ga tekshirish
                    result = await check_essay_text(text, criteria, topic)
                else:
                    result = "⚠️ Iltimos, esse matnini yozing yoki rasm yuklang!"
            except Exception as e:
                result = f"Xatolik yuz berdi: {str(e)}"
            
            # Natijani Telegram orqali yuborish
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": result, "parse_mode": "Markdown"}
            )
            
        # Asinxron tarzda AIni ishga tushirish (Webapp qotib qolmasligi uchun)
        asyncio.create_task(process_and_send())
        
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
