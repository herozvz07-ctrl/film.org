import os
from flask import Flask, request
import telebot
from telebot import types
from pymongo import MongoClient

# ---------------- CONFIG ----------------
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

CHANNELS = [
    "@StudioFilm_org"
]

FILM_CHANNEL = "@only_filimlar"
MENU_IMAGE = "https://your-image-link.jpg"
FILM_LINK = "https://t.me/only_filimlar"

MONGO_URL = "mongodb+srv://herozvz07_db_user:iXi80aUXy9qUtPcP@cluster0.bb0wzws.mongodb.net/?appName=Cluster0"

# ---------------- BOT ----------------
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

client = MongoClient(MONGO_URL)
db = client["film_bot"]
films = db["films"]

# ---------------- WEBHOOK ----------------
@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ---------------- FUNCTIONS ----------------

def check_sub(user_id):
    for ch in CHANNELS:
        try:
            s = bot.get_chat_member(ch, user_id).status
            if s not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_keyboard():
    kb = types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        kb.add(types.InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
    return kb

def send_menu(chat_id, name):
    bot.send_photo(
        chat_id,
        MENU_IMAGE,
        caption=f"👋 Asalomu Aleykum {name}, botimizga xush kelibsiz!\n\n🔎 Endi kerakli <a href='{FILM_LINK}'>filmning</a> kodini yuboring.",
        parse_mode="HTML"
    )

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❗ Iltimos obuna bo‘ling:", reply_markup=sub_keyboard())
    else:
        send_menu(msg.chat.id, msg.from_user.first_name)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_menu(call.message.chat.id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali obuna emassiz!")

# ---------------- ADD FILM (ADMIN) ----------------
@bot.channel_post_handler(func=lambda m: m.chat.username == FILM_CHANNEL.replace("@",""))
def save_film(m):
    if m.text:
        code = m.text.split("\n")[0]
        films.insert_one({
            "code": code.lower(),
            "message_id": m.message_id
        })

# ---------------- GET FILM ----------------
@bot.message_handler(func=lambda m: True)
def get_film(m):
    if not check_sub(m.from_user.id):
        bot.send_message(m.chat.id, "❗ Iltimos obuna bo‘ling:", reply_markup=sub_keyboard())
        return

    code = m.text.lower()
    film = films.find_one({"code": code})

    if not film:
        bot.send_message(m.chat.id, "❌ Film topilmadi")
        return

    bot.copy_message(
        chat_id=m.chat.id,
        from_chat_id=FILM_CHANNEL,
        message_id=film["message_id"]
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
