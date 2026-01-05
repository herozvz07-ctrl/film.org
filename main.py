import os
import asyncio
import requests
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

REQUIRED_CHANNELS = ["@StudioFilm_org"]
FILM_CHANNEL = "@only_filimlar"

MENU_IMAGE = "https://i.postimg.cc/7ZN8r33G/40b3a7667c57b37bb66735d67609798e.jpg"
CHANNEL_LINK = "https://t.me/only_filimlar"

# ---------------- MongoDB Data API ----------------
MONGO_APP_ID = "PASTE_APP_ID"
MONGO_API_KEY = "PASTE_API_KEY"
MONGO_CLUSTER = "Cluster0"
MONGO_DB = "film_bot"
MONGO_COLLECTION = "films"

MONGO_URL = f"https://data.mongodb-api.com/app/{MONGO_APP_ID}/endpoint/data/v1/action"
HEADERS = {
    "Content-Type": "application/json",
    "api-key": MONGO_API_KEY
}

# ---------------- BOT ----------------
bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)

# ---------------- Mongo Functions ----------------
def save_film(code, message_id):
    requests.post(MONGO_URL + "/insertOne", json={
        "dataSource": MONGO_CLUSTER,
        "database": MONGO_DB,
        "collection": MONGO_COLLECTION,
        "document": {
            "code": code,
            "message_id": message_id
        }
    }, headers=HEADERS)

def get_film(code):
    r = requests.post(MONGO_URL + "/findOne", json={
        "dataSource": MONGO_CLUSTER,
        "database": MONGO_DB,
        "collection": MONGO_COLLECTION,
        "filter": {"code": code}
    }, headers=HEADERS)
    return r.json().get("document")

# ---------------- Subscription ----------------
async def check_sub(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            s = (await bot.get_chat_member(ch, user_id)).status
            if s not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def sub_kb():
    kb = InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        kb.add(InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
    return kb

# ---------------- START ----------------
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    if not await check_sub(m.from_user.id):
        await m.answer("❗ Iltimos, obuna bo‘ling:", reply_markup=sub_kb())
    else:
        await bot.send_photo(
            m.chat.id,
            MENU_IMAGE,
            caption=f"👋 Assalomu alaykum {m.from_user.first_name}!\n\n🔎 Endi <a href='{CHANNEL_LINK}'>kerakli filmning</a> kodini yuboring.",
            parse_mode="HTML"
        )

@dp.callback_query_handler(lambda c: c.data == "check")
async def check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await start(call.message)
    else:
        await call.answer("❌ Obuna bo‘lmadingiz")

# ---------------- Save Films ----------------
@dp.channel_post_handler(lambda m: m.chat.username == FILM_CHANNEL.replace("@",""))
async def save_channel(m: types.Message):
    if m.text:
        code = m.text.split("\n")[0].lower()
        save_film(code, m.message_id)

# ---------------- Get Film ----------------
@dp.message_handler()
async def get_movie(m: types.Message):
    if not await check_sub(m.from_user.id):
        await m.answer("❗ Obuna bo‘ling", reply_markup=sub_kb())
        return

    film = get_film(m.text.lower())
    if not film:
        await m.answer("❌ Film topilmadi")
        return

    await bot.copy_message(m.chat.id, FILM_CHANNEL, film["message_id"])

# ---------------- WEBHOOK ----------------
@app.route("/", methods=["POST"])
def webhook():
    update = types.Update.de_json(request.get_json(force=True))
    asyncio.run(dp.process_update(update))
    return "OK"

# ---------------- RUN ----------------
if __name__ == "__main__":
    WEBHOOK_URL = os.environ["RENDER_EXTERNAL_URL"] + "/"
    asyncio.run(bot.set_webhook(WEBHOOK_URL))
    app.run(host="0.0.0.0", port=10000)
