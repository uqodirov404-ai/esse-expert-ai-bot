import json
import logging
import asyncio
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from config import BOT_TOKEN, WEBAPP_URL
import database as db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = 162634410

async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    channels = db.get_channels()
    if not channels: return True
    is_sub = True
    keyboard = []
    for cid, title, url in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=cid, user_id=user_id)
            if member.status in ['left', 'kicked']:
                is_sub = False
                keyboard.append([InlineKeyboardButton(title, url=url)])
        except Exception:
            is_sub = False
            keyboard.append([InlineKeyboardButton(title, url=url)])
    if not is_sub:
        keyboard.append([InlineKeyboardButton("Tasdiqlash ✅", callback_data="check_sub_btn")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz majburiy:"
        if update.message:
            await update.message.reply_text(msg, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user.id, user.first_name, user.username)
    if not await check_sub(update, context): return
    
    welcome_text = (
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Barcha xizmatlardan foydalanish uchun quyidagi tugmani bosing va Ilovaga kiring:"
    )
    
    # Eskidan qolgan klaviaturalarni tozalash uchun qisqa xabar yuboramiz
    await update.message.reply_text("Ilova yuklanmoqda...", reply_markup=ReplyKeyboardRemove())
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Ilovaga kirish", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = update.effective_user
    
    if data == "check_sub_btn":
        if await check_sub(update, context):
            await query.message.delete()
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Ilovaga kirish", web_app=WebAppInfo(url=WEBAPP_URL))]])
            await query.message.reply_text("Rahmat! Endi ilovaga kirishingiz mumkin.", reply_markup=keyboard)
        return

    if not await check_sub(update, context): return

    if data.startswith("exp_accept_") and user.id == ADMIN_ID:
        exp_id = int(data.split("_")[2])
        db.update_expert_status(exp_id, "active")
        await query.edit_message_text("Ekspert qabul qilindi!")
        try:
            await context.bot.send_message(chat_id=exp_id, text="Ekspertlik arizangiz qabul qilindi! Ilova orqali kabinetingizga kirishingiz mumkin.")
        except: pass
        
    elif data.startswith("exp_reject_") and user.id == ADMIN_ID:
        exp_id = int(data.split("_")[2])
        db.update_expert_status(exp_id, "rejected")
        await query.edit_message_text("Ekspert rad etildi.")
        
    elif data.startswith("pay_ok_") and user.id == ADMIN_ID:
        essay_id = int(data.split("_")[2])
        essay = db.get_human_essay(essay_id)
        if essay:
            db.update_human_essay_status(essay_id, "checking")
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ To'lov tasdiqlandi!")
            try:
                await context.bot.send_message(chat_id=essay[1], text=f"✅ To'lov tasdiqlandi!\nEssengiz (ID: {essay_id}) ekspertga yuborildi.")
                await context.bot.send_message(chat_id=essay[2], text=f"🔔 Yangi esse keldi! Ilovadagi 'Kabinet'ingizni tekshiring.")
            except: pass
            
    elif data.startswith("pay_no_") and user.id == ADMIN_ID:
        essay_id = int(data.split("_")[2])
        db.update_human_essay_status(essay_id, "rejected")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ To'lov rad etildi!")

    await query.answer()

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Just redirect them to the Web App if they type anything
    if not await check_sub(update, context): return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Ilovaga kirish", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await update.message.reply_text("Iltimos, xizmatlardan foydalanish uchun ilovaga kiring:", reply_markup=keyboard)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, any_message))
    logger.info("Bot ishga tushmoqda...")
    app.run_polling(stop_signals=())

if __name__ == "__main__":
    main()
