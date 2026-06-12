import json
import logging
import asyncio
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from config import BOT_TOKEN, WEBAPP_URL
import database as db
import ai_engine

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i. WebApp tugmasini ko'rsatadi."""
    user = update.effective_user
    await asyncio.to_thread(db.save_user, user.id, user.first_name, user.username)
    
    count = await asyncio.to_thread(db.get_stats, user.id)
    
    # WebApp tugmasi
    keyboard = [
        [KeyboardButton("✍️ Esse Yozish (Web App)", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Men sizning shaxsiy <b>Esse Ekspert</b>ingizman (Sun'iy Intellekt).\n\n"
        "Quyidagi usullar bilan essengizni tekshirishingiz mumkin:\n"
        "1️⃣ Pastdagi <b>'✍️ Esse Yozish'</b> tugmasini bosib, matnni kiritish.\n"
        "2️⃣ Yoki menga to'g'ridan-to'g'ri <b>qo'lyozma essengiz rasmini</b> tashlash.\n\n"
        f"📊 Siz shu paytgacha {count} ta esse tekshirgansiz."
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Web App dan kelgan ma'lumotni ushlab oladi"""
    try:
        data_str = update.effective_message.web_app_data.data
        data = json.loads(data_str)
        
        criteria = data.get("criteria", "milliy")
        topic = data.get("topic", "Mavzu kiritilmagan")
        essay_text = data.get("essay", "")
        
        if len(essay_text.split()) < 10:
            await update.message.reply_text("⚠️ Essengiz juda qisqa. Kamida 10 ta so'z bo'lishi kerak.")
            return

        msg = await update.message.reply_text("⏳ <i>Essengiz AI tomonidan tahlil qilinmoqda... Iltimos kuting (15-30 soniya)</i>", parse_mode="HTML")
        
        # AI ga yuborish
        result = await ai_engine.check_essay_text(topic, essay_text, criteria)
        
        # Bazaga saqlash
        await asyncio.to_thread(db.save_essay, update.effective_user.id, topic, criteria, essay_text, result)
        
        # Javobni yuborish (juda uzun bo'lsa bo'lib yuborish kerak, lekin odatda 4096 belgidan oshmaydi)
        await msg.edit_text(result)
        
    except Exception as e:
        logger.error(f"WebApp Data xatosi: {e}")
        await update.message.reply_text("⚠️ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasmlarni ushlab oladi va mezon so'raydi"""
    photo_file = await update.message.photo[-1].get_file()
    
    # Rasmni yuklab olish
    file_path = f"essay_{update.effective_user.id}.jpg"
    await photo_file.download_to_drive(file_path)
    
    # State ni saqlash (qaysi rasm ustida ishlayotganini bilish uchun)
    context.user_data['last_image_path'] = file_path
    
    keyboard = [
        [InlineKeyboardButton("Milliy Sertifikat", callback_data="crit_milliy")],
        [InlineKeyboardButton("IELTS", callback_data="crit_ielts"), InlineKeyboardButton("CEFR", callback_data="crit_cefr")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Qo'lyozma qabul qilindi! ✅\nQaysi mezon bo'yicha tekshiray?", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugma bosilganda"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("crit_"):
        criteria = data.split("_")[1]
        image_path = context.user_data.get('last_image_path')
        
        if not image_path:
            await query.edit_message_text("⚠️ Rasm muddati tugagan yoki topilmadi. Boshqatdan yuboring.")
            return
            
        await query.edit_message_text("⏳ <i>Qo'lyozma o'qilmoqda va tahlil qilinmoqda... Kuting!</i>", parse_mode="HTML")
        
        # AI Vision tahlili
        result = await ai_engine.check_essay_image(image_path)
        
        # Bazaga saqlash
        await asyncio.to_thread(db.save_essay, update.effective_user.id, "Qo'lyozma Rasm", criteria, "[Rasm]", result)
        
        # Natija
        # Uzun natijalarni telegram qabul qilmasligi mumkin, shuning uchun kesamiz agar kerak bo'lsa
        if len(result) > 4000:
            await query.message.reply_text(result[:4000])
            await query.message.reply_text(result[4000:])
        else:
            await query.message.reply_text(result)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Bot ishga tushmoqda...")
    app.run_polling()

if __name__ == "__main__":
    main()
