from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# Bosqichlar
MANZIL, TELEFON = range(2)

ADMIN_CHAT_ID = [513886700, 2075436847, 1079017251, 258140265, 8020357796]  # Hozirgi adminlar ro'yxati

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Andijon ➔ Samarqand")],
        [KeyboardButton("Samarqand ➔ Andijon")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "Salom! Qayerdan qayerga borasiz?", reply_markup=reply_markup
    )
    return MANZIL

# Manzilni button orqali qabul qilish
async def manzil_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['manzil'] = update.message.text
    # Telefon raqamini matnli tarzda so‘raymiz, klaviaturani yopamiz
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

    # Buyurtmani admin/operatorga yuborish
    msg = f"🚕 Yangi buyurtma!\nManzil: {manzil}\nTelefon: {telefon}"
    for admin_id in ADMIN_CHAT_ID:
        await context.bot.send_message(chat_id=admin_id, text=msg)

    await update.message.reply_text("Buyurtmangiz qabul qilindi! Shafiyor siz bilan tez orada bog‘lanadi.", reply_markup=None)
    return ConversationHandler.END

# Bekor qilish
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buyurtma bekor qilindi.", reply_markup=None)
    return ConversationHandler.END

# /myid komandasi uchun funksiya
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning chat ID: {update.message.chat.id}")

if __name__ == '__main__':
    app = ApplicationBuilder().token('8087242928:AAEp3ljXsI4XbPC_2jLS1IfuCscznRDohJY').build()

    app.add_handler(CommandHandler('myid', myid))

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


