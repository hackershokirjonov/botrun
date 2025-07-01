import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv
import sys

# .env faylidan bot tokenini yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# data.json faylidan do‘konlar ro‘yxatini yuklaymiz
try:
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    shops = data.get('shops', [])
except FileNotFoundError:
    print("Xato: data.json fayli topilmadi!")
    sys.exit(1)
except json.JSONDecodeError:
    print("Xato: data.json fayli noto‘g‘ri formatda!")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not shops:
        await update.message.reply_text("❗ Hozirda do‘konlar mavjud emas. Keyinroq urinib ko‘ring.")
        return

    keyboard = [
        [InlineKeyboardButton(shop['name'], callback_data=shop['id'])] for shop in shops
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Kerakli do‘konni tanlang:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    shop_id = query.data
    selected_shop = next((s for s in shops if s['id'] == shop_id), None)
    
    if selected_shop:
        context.user_data['selected_shop'] = selected_shop
        msg = (
            f"🏪 Do‘kon: {selected_shop['name']}\n"
            f"💳 To‘lov karta raqami: {selected_shop['card']}\n\n"
            "Iltimos, to‘lovni amalga oshiring va quyidagi ma'lumotlarni yuboring:\n"
            "- 📸 To‘lov screenshot\n- 👤 Ism Familiya\n- 🧾 Buyurtma raqami\n- 🙋‍♀🙋‍♂ Savollar yoki Fikrlaringizni qoldiring"
        )
        await query.message.reply_text(msg)
    else:
        await query.message.reply_text("❗ Do‘kon topilmadi. Iltimos, /start ni qayta bosing.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    shop = context.user_data.get('selected_shop')

    if not shop:
        await update.message.reply_text("❗ Iltimos, avval do‘konni tanlang /start")
        return

    admin_id = shop['admin_id']
    caption_text = update.message.caption if update.message.caption else ""
    message_text = update.message.text if update.message.text else ""
    info_text = caption_text or message_text or "Ma'lumot mavjud emas."

    text = (
        f"🆕 Yangi to‘lov ma'lumoti\n"
        f"👤 Foydalanuvchi: @{user.username or user.first_name}\n"
        f"🏪 Do‘kon: {shop['name']}\n"
        f"📥 Ma'lumot: {info_text}\n"
        f"🕒 Vaqt: {update.message.date}"
    )

    try:
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=admin_id, photo=photo_file_id, caption=text)
        else:
            await context.bot.send_message(chat_id=admin_id, text=text)
        
        await update.message.reply_text("✅ Ma'lumotlar yuborildi. Do‘kon admini tez orada siz bilan bog‘lanadi.")
    except Exception as e:
        await update.message.reply_text("❌ Xato yuz berdi. Iltimos, qaytadan urinib ko‘ring.")
        print(f"Xato admin ID {admin_id} ga xabar yuborishda: {e}")

def main():
    if not BOT_TOKEN:
        print("Xato: Bot tokeni topilmadi! .env faylida BOT_TOKEN ni sozlang.")
        sys.exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_message))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
