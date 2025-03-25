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

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        # Tạo event loop mới cho mỗi request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_update(update))
        return "OK", 200
    except Exception as e:
        print("Error in webhook:", e)
        return str(e), 500

async def handle_update(update: Update):
    if update.message and update.message.text:
        if update.message.text.strip() == "/start":
            await update.message.reply_text("Xin chàoooooo!")
        else:
            print("Received message:", update.message.text)
    else:
        print("No valid message in update.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
