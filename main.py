import os
import json
import hmac
import hashlib
from urllib.parse import parse_qsl
import aiofiles
from fastapi import FastAPI, Request, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import asyncio
import threading
from typing import List

from config import BOT_TOKEN
from ai_engine import check_essay_text, check_essay_image
import bot
import database as db

app = FastAPI()
from fastapi.staticfiles import StaticFiles
app.mount('/static', StaticFiles(directory='webapp'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_init_data(init_data: str) -> dict:
    try:
        parsed_data = dict(parse_qsl(init_data))
        if 'hash' not in parsed_data:
            return None
            
        hash_val = parsed_data.pop('hash')
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == hash_val:
            user_data = json.loads(parsed_data.get('user', '{}'))
            return user_data
    except Exception as e:
        pass
    return None

async def keep_alive():
    while True:
        try:
            requests.get("https://esse-expert-ai-bot.onrender.com/")
        except:
            pass
        await asyncio.sleep(840)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

@app.get("/")
async def read_index():
    with open("webapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/user")
async def get_user(request: Request):
    data = await request.json()
    user_data = validate_init_data(data.get("initData", ""))
    if not user_data:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    user_id = user_data.get("id")
    first_name = user_data.get("first_name", "User")
    username = user_data.get("username", "")
    db.save_user(user_id, first_name, username)
    
    stats = db.get_stats(user_id)
    user_db = db.get_user(user_id)
    balance = user_db[3] if user_db and len(user_db) > 3 else 0
    exp_db = db.get_expert(user_id)
    
    expert_info = None
    if exp_db:
        expert_info = {
            "status": exp_db[1],
            "bio": exp_db[2],
            "rating": exp_db[3],
            "reviews": exp_db[4],
            "earned": exp_db[5]
        }
        
    return {
        "id": user_id,
        "first_name": first_name,
        "stats": stats,
        "balance": balance,
        "expert": expert_info,
        "is_admin": user_id == bot.ADMIN_ID
    }

@app.get("/api/experts")
async def get_experts():
    experts = db.get_active_experts()
    return [{"id": e[0], "name": e[1], "bio": e[2], "rating": e[3], "reviews": e[4]} for e in experts]

@app.get("/api/settings")
async def get_settings():
    price = db.get_setting("expert_price") or "20000"
    card = db.get_setting("payment_card") or "Kiritilmagan"
    return {"price": price, "card": card}

@app.post("/api/upload_ai")
async def upload_ai(
    initData: str = Form(...),
    criteria: str = Form(...),
    topic: str = Form(""),
    text: str = Form(""),
    files: List[UploadFile] = File(None)
):
    user_data = validate_init_data(initData)
    if not user_data: raise HTTPException(status_code=401)
    user_id = user_data.get("id")
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": user_id, "text": "⏳ AI essengizni tekshirmoqda..."})
    
    async def process():
        result = ""
        file_paths = []
        try:
            if files and len(files) > 0 and files[0].filename:
                for file in files:
                    path = f"temp_{user_id}_{file.filename}"
                    file_paths.append(path)
                    async with aiofiles.open(path, 'wb') as out_file:
                        content = await file.read()
                        await out_file.write(content)
                result = await check_essay_image(file_paths)
            elif text:
                result = await check_essay_text(text, criteria, topic)
            else:
                result = "⚠️ Iltimos, esse yozing yoki rasm yuklang!"
        except Exception as e:
            result = f"Xatolik: {str(e)}"
        finally:
            for p in file_paths:
                if os.path.exists(p): os.remove(p)
                
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": user_id, "text": result, "parse_mode": "Markdown"})
        
    asyncio.create_task(process())
    return {"status": "ok"}

@app.post("/api/upload_human")
async def upload_human(
    initData: str = Form(...),
    expert_id: int = Form(...),
    text: str = Form(""),
    files: List[UploadFile] = File(None),
    receipt: UploadFile = File(...)
):
    user_data = validate_init_data(initData)
    if not user_data: raise HTTPException(status_code=401)
    user_id = user_data.get("id")
    price = int(db.get_setting("expert_price") or "20000")
    
    receipt_path = f"temp_receipt_{user_id}_{receipt.filename}"
    async with aiofiles.open(receipt_path, 'wb') as f:
        await f.write(await receipt.read())
        
    # Send receipt to admin
    with open(receipt_path, 'rb') as photo:
        res = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": bot.ADMIN_ID, "caption": f"To'lov cheki. Summa: {price} UZS"},
            files={"photo": photo}
        )
    os.remove(receipt_path)
    photo_file_id = res.json().get("result", {}).get("photo", [{}])[-1].get("file_id", "")
    
    essay_id = db.create_human_essay(user_id, expert_id, "Kutilmoqda", "Kutilmoqda", "", "", price)
    db.update_human_essay_receipt(essay_id, photo_file_id)
    
    # Send essay to admin for approval via callback_data
    keyboard = {"inline_keyboard": [[
        {"text": "Tasdiqlash", "callback_data": f"pay_ok_{essay_id}"},
        {"text": "Rad etish", "callback_data": f"pay_no_{essay_id}"}
    ]]}
    
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup", json={
        "chat_id": bot.ADMIN_ID,
        "message_id": res.json()["result"]["message_id"],
        "reply_markup": keyboard
    })
    
    # Temporarily store text/images (since payment needs approval first, we just store it now or save in DB)
    if text:
        with db.get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE essays_human SET essay_text=%s WHERE id=%s", (text, essay_id))
            conn.commit()
    
    if files and len(files) > 0 and files[0].filename:
        photo_ids = []
        for file in files:
            path = f"temp_{user_id}_{file.filename}"
            async with aiofiles.open(path, 'wb') as f:
                await f.write(await file.read())
            
            # Send photo to bot itself to get file_id
            with open(path, 'rb') as photo:
                pres = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={"chat_id": user_id, "caption": "Vaqtincha"},
                    files={"photo": photo}
                )
            os.remove(path)
            pid = pres.json().get("result", {}).get("photo", [{}])[-1].get("file_id", "")
            if pid: photo_ids.append(pid)
            
        with db.get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE essays_human SET photo_file_id=%s WHERE id=%s", (json.dumps(photo_ids), essay_id))
            conn.commit()

    return {"status": "ok", "message": "Chek va esse yuborildi. Admin tasdiqlashi kutilmoqda."}

@app.post("/api/apply_expert")
async def apply_expert(request: Request):
    data = await request.json()
    user_data = validate_init_data(data.get("initData", ""))
    if not user_data: raise HTTPException(status_code=401)
    
    db.add_expert_application(user_data["id"], data.get("bio", ""))
    
    # Notify admin
    keyboard = {"inline_keyboard": [
        [{"text": "Qabul", "callback_data": f"exp_accept_{user_data['id']}"}, {"text": "Rad", "callback_data": f"exp_reject_{user_data['id']}"}],
        [{"text": "Xabar yozish", "callback_data": f"exp_msg_{user_data['id']}"}]
    ]}
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": bot.ADMIN_ID,
        "text": f"🆕 Yangi Ekspert Arizasi\nFoydalanuvchi: {user_data.get('first_name')}\nBio: {data.get('bio')}",
        "reply_markup": keyboard
    })
    return {"status": "ok"}

@app.get("/api/expert/tasks")
async def expert_tasks(request: Request):
    initData = request.query_params.get("initData", "")
    user_data = validate_init_data(initData)
    if not user_data: raise HTTPException(status_code=401)
    
    essays = db.get_expert_pending_essays(user_data["id"])
    if not essays: return []
    
    res = []
    for e in essays:
        # e = (id, user_id, expert_id, status, created_at, essay_text, photo_file_id, total_price, text_reply, rating)
        res.append({
            "id": e[0],
            "text": e[5],
            "photo_id": e[6]
        })
    return res

@app.post("/api/expert/reply")
async def expert_reply(request: Request):
    data = await request.json()
    user_data = validate_init_data(data.get("initData", ""))
    if not user_data: raise HTTPException(status_code=401)
    
    essay_id = data.get("essay_id")
    reply_text = data.get("reply_text")
    essay = db.get_human_essay(essay_id)
    
    if essay and essay[2] == user_data["id"]:
        db.finish_human_essay(essay_id, 0, reply_text)
        
        # Notify user
        msg = f"👨‍🏫 <b>Ekspert javobi:</b>\n\n{reply_text}"
        keyboard = {"inline_keyboard": [[
            {"text": f"{i}⭐", "callback_data": f"rate_{user_data['id']}_{i}"} for i in range(1, 6)
        ]]}
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": essay[1],
            "text": msg,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        })
        return {"status": "ok"}
    raise HTTPException(status_code=400)

@app.post("/api/admin/settings")
async def update_settings(request: Request):
    data = await request.json()
    user_data = validate_init_data(data.get("initData", ""))
    if not user_data or user_data["id"] != bot.ADMIN_ID: raise HTTPException(status_code=401)
    
    if "price" in data: db.set_setting("expert_price", data["price"])
    if "card" in data: db.set_setting("payment_card", data["card"])
    return {"status": "ok"}

@app.post("/api/admin/remove_expert")
async def remove_expert(request: Request):
    data = await request.json()
    user_data = validate_init_data(data.get("initData", ""))
    if not user_data or user_data["id"] != bot.ADMIN_ID: raise HTTPException(status_code=401)
    
    exp_id = data.get("expert_id")
    db.update_expert_status(exp_id, "rejected")
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": exp_id, "text": "Sizning ekspertlik huquqingiz admin tomonidan bekor qilindi."
        })
    except: pass
    return {"status": "ok"}

def run_telegram_bot():
    bot.main()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


