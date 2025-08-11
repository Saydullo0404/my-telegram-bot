from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import logging
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()  # agar .env fayl ishlatsangiz, shu orqali yuklaydi

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- States ---
MANZIL, TELEFON = range(2)

# --- Config ---
ADMIN_CHAT_ID = {513886700, 2075436847, 1079017251, 258140265, 8020357796}
USERS_FILE = "users.json"   # /start bosgan userlar
ORDERS_FILE = "orders.json" # buyurtmalar logi

# --- Storage helpers ---
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_users():
    return set(load_json(USERS_FILE, []))

def save_user(user_id: int):
    users = get_users()
    if user_id not in users:
        users.add(user_id)
        save_json(USERS_FILE, list(users))

def append_order(order: dict):
    orders = load_json(ORDERS_FILE, [])
    orders.append(order)
    save_json(ORDERS_FILE, orders)

# --- Utils ---
PHONE_RE = re.compile(r"^\+?\d[\d\s\-()]{6,}$")

def normalize_phone(text: str) -> str:
    return re.sub(r"[^\d+]", "", text)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_CHAT_ID

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        save_user(user.id)

    keyboard = [
        [KeyboardButton("Andijon ➔ Samarqand")],
        [KeyboardButton("Samarqand ➔ Andijon")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.effective_message.reply_text(
        "Salom! Qayerdan qayerga borasiz?", reply_markup=reply_markup
    )
    return MANZIL

async def manzil_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return MANZIL

    context.user_data["manzil"] = update.message.text.strip()

    keyboard = [
        [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)],
        [KeyboardButton("⬅️ Ortga")]
    ]
    await update.message.reply_text(
        "Telefon raqamingizni yuboring yoki tugma orqali ulashing:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return TELEFON

async def telefon_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text == "⬅️ Ortga":
        return await start(update, context)

    phone = None
    if update.message and update.message.contact and update.message.contact.phone_number:
        phone = update.message.contact.phone_number
    elif update.message and update.message.text:
        candidate = update.message.text.strip()
        if PHONE_RE.match(candidate):
            phone = normalize_phone(candidate)

    if not phone:
        await update.message.reply_text(
            "Iltimos, to‘g‘ri telefon raqam yuboring yoki “📞 Telefon raqamni yuborish” tugmasidan foydalaning."
        )
        return TELEFON

    context.user_data["telefon"] = phone
    manzil = context.user_data.get("manzil", "—")
    user = update.effective_user

    append_order({
        "user_id": user.id if user else None,
        "manzil": manzil,
        "telefon": phone,
        "ts": datetime.utcnow().isoformat()
    })

    msg = f"🚕 Yangi buyurtma!\nManzil: {manzil}\nTelefon: {phone}"
    for admin_id in ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=admin_id, text=msg)
        except Exception as e:
            logger.warning(f"Adminga yuborishda xatolik ({admin_id}): {e}")

    await update.message.reply_text(
        "Buyurtmangiz qabul qilindi! Haydovchi tez orada siz bilan bog‘lanadi.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Buyurtma bekor qilindi.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"Sizning chat ID: {update.effective_chat.id}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    users = get_users()
    orders = load_json(ORDERS_FILE, [])

    today = datetime.utcnow().date()
    today_count = sum(1 for o in orders if datetime.fromisoformat(o["ts"]).date() == today)

    text = (
        "📊 *Bot statistikasi*\n"
        f"👥 /start bosganlar: *{len(users)}*\n"
        f"🧾 Jami buyurtmalar: *{len(orders)}*\n"
        f"🗓️ Bugungi buyurtmalar: *{today_count}*\n"
    )
    await update.effective_message.reply_markdown(text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Xatolik yuz berdi: %s", context.error)

def main():
    token = os.getenv("BOT_TOKEN")  # Environment o'zgaruvchisidan oladi
    if not token:
        raise RuntimeError("BOT_TOKEN environment o‘zgaruvchisini o‘rnating!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MANZIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, manzil_qabul)],
            TELEFON: [
                MessageHandler(filters.CONTACT, telefon_qabul),
                MessageHandler(filters.TEXT & ~filters.COMMAND, telefon_qabul),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv_handler)

    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
