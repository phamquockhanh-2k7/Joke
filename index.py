import telegram
import asyncio
from flask import Flask, request
from telegram import Update

BOT_TOKEN = "8064426886:AAHNez92dmsVQBB6yQp65k_pjPwiJT-SBEI"

app = Flask(__name__)
bot = telegram.Bot(token=BOT_TOKEN)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# Endpoint webhook: Telegram sẽ gửi POST request vào đây
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_update(update))
    return "OK"

# Xử lý tin nhắn được gửi đến
async def handle_update(update: Update):
    if update.message and update.message.text.strip() == "/start":
        await update.message.reply_text("Xin chào!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
