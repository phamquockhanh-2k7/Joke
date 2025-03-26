from flask import Flask, request
from telegram import Bot, Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext
import asyncio
import nest_asyncio
import random
import requests
import os

nest_asyncio.apply()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = "https://vuotlink.vip/api"
bot = Bot(token=BOT_TOKEN)
media_groups = {}
processing_tasks = {}

@app.route('/', methods=['GET'])
def home():
    return "Bot is alive!"

@app.route('/', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        asyncio.run(process_update(update))
        return "OK", 200

async def process_update(update: Update):
    if update.message:
        if update.message.text and update.message.text.startswith("/start"):
            await start(update, None)
        elif update.message.text and update.message.text.startswith("http"):
            await shorten_link(update, None)
        elif update.message.photo or update.message.video:
            await handle_media(update)

async def start(update: Update, context: CallbackContext):
    if not update.message or update.effective_chat.type != "private":
        return  

    await update.message.reply_text(
        "**👋 Chào mừng bạn!**\n\n"
        "**🔗 Gửi link bất kỳ để rút gọn.**\n"
        "**📷 Chuyển tiếp bài viết kèm ảnh/video, bot sẽ giữ nguyên caption & rút gọn link trong caption.**\n"
        "**💬 Mọi thắc mắc, hãy liên hệ admin.**",
        parse_mode="Markdown"
    )

async def format_text(text: str) -> str:
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        words = line.split()
        new_words = []
        for word in words:
            if word.startswith("http"):
                params = {"api": API_KEY, "url": word, "format": "text"}
                response = requests.get(API_URL, params=params)
                short_link = response.text.strip() if response.status_code == 200 else word
                word = f"<s>{short_link}</s>"
            else:
                word = f"<b>{word}</b>"
            new_words.append(word)
        new_lines.append(" ".join(new_words))

    new_lines.append(
        '\n<b>Báo lỗi + đóng góp video tại đây</b> @nothinginthissss (có lỗi sẽ đền bù)\n'
        '<b>Theo dõi thông báo tại đây</b> @sachkhongchuu\n'
        '<b>CÁCH XEM LINK:</b> @HuongDanVuotLink_SachKhongChu\n\n'
        '⚠️<b>Kênh xem không cần vượt :</b> <a href="https://t.me/sachkhongchuu/299">ấn vào đây</a>'
    )
    return "\n".join(new_lines)

async def shorten_link(update: Update, context: CallbackContext):
    if not update.message:
        return  

    if update.message.text and update.message.text.startswith("http"):
        params = {"api": API_KEY, "url": update.message.text.strip(), "format": "text"}
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            short_link = response.text.strip()
            message = (
                "📢 <b>Bạn có link rút gọn mới</b>\n"
                f"🔗 <b>Link gốc:</b> <s>{update.message.text}</s>\n"
                f"🔍 <b>Link rút gọn:</b> <s>{short_link}</s>\n\n"
                '⚠️<b>Kênh xem không cần vượt :</b> <a href="https://t.me/sachkhongchuu/299">ấn vào đây</a>'
            )
            await update.message.reply_text(message, parse_mode="HTML")

async def handle_media(update: Update):
    if not update.message or not (update.message.photo or update.message.video):
        return  

    text = update.message.caption or ""
    if text:
        formatted_text = await format_text(text)
        if update.message.photo:
            await bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=update.message.photo[-1].file_id,
                caption=formatted_text,
                parse_mode="HTML"
            )
        elif update.message.video:
            await bot.send_video(
                chat_id=update.effective_chat.id,
                video=update.message.video.file_id,
                caption=formatted_text,
                parse_mode="HTML"
            )
    else:
        if update.message.photo:
            await bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=update.message.photo[-1].file_id
            )
        elif update.message.video:
            await bot.send_video(
                chat_id=update.effective_chat.id,
                video=update.message.video.file_id
            )

if __name__ == "__main__":
    app.run()
