from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import logging
import json
import os

# Bosqichlar
MANZIL, TELEFON = range(2)

# Admin chat id-lari
ADMIN_CHAT_ID = [513886700, 2075436847, 1079017251, 258140265, 8020357796]

# Foydalanuvchilar start bosganini saqlash uchun fayl
USERS_FILE = "users.json"

# Logging sozlash
logging.basicConfig(level=logging.INFO)

# Foydalanuvchilarni o'qish va yozish uchun yordamchi funksiya
def get_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(json.load(f))

def save_user(user_id):
    users = get_users()
    users.add(user_id)
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    save_user(user_id)
    keyboard = [
        [KeyboardButton("Andijon ➔ Samarqand")],
        [KeyboardButton("Samarqand ➔ Andijon")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Salom! Qayerdan qayerga borasiz?", reply_markup=reply_markup
    )
    return MANZIL

# Manzilni qabul qilish
async def manzil_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['manzil'] = update.message.text
    await update.message.reply_text(
        "Telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return TELEFON

# Telefon raqamni qabul qilish
async def telefon_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ Ortga":
        return await start(update, context)
    context.user_data['telefon'] = update.message.text
    manzil = context.user_data['manzil']
    telefon = context.user_data['telefon']

    # Adminlarga yuborish
    msg = f"🚕 Yangi buyurtma!\nManzil: {manzil}\nTelefon: {telefon}"
    for admin_id in ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=admin_id, text=msg)
    await update.message.reply_text("Buyurtmangiz qabul qilindi! Shafyor siz bilan tez orada bog'lanadi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Bekor qilish
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buyurtma bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# /myid komandasi
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning chat ID: {update.message.chat.id}")

# /stats komandasi - start bosganlar soni
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_users()
    await update.message.reply_text(f"Botga /start bosgan foydalanuvchilar soni: {len(users)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token('8087242928:AAEp3ljXsI4XbPC_2jLS1IfuCscznRDohJY').build()

    # Handlerlar
    app.add_handler(CommandHandler('myid', myid))
    app.add_handler(CommandHandler('stats', stats))  # Stats handler (faqat adminlarga ochiq qilishni xohlasa, tekshiruv qo'shish mumkin)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MANZIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, manzil_qabul)],
            TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, telefon_qabul)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


