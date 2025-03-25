import requests
import telegram
import asyncio
import random
from flask import Flask, request
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import CallbackContext

# Cài đặt token và API
BOT_TOKEN = "8064426886:AAHNez92dmsVQBB6yQp65k_pjPwiJT-SBEI"
API_KEY = "5d2e33c19847dea76f4fdb49695fd81aa669af86"
API_URL = "https://vuotlink.vip/api"

app = Flask(__name__)
bot = telegram.Bot(token=BOT_TOKEN)
media_groups = {}
processing_tasks = {}

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

# Route webhook: Telegram sẽ gửi dữ liệu POST vào đây
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # Tạo event loop mới cho mỗi request để tránh lỗi trong môi trường serverless
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_update(update))
    return "OK"

# Xử lý lệnh /start nếu tin nhắn chứa lệnh (Telegram sẽ gửi lệnh này qua webhook)
async def start(update: Update, context: CallbackContext):
    if not update.message:
        return
    if update.effective_chat.type != "private":
        return
    await update.message.reply_text(
        "**👋 Chào mừng bạn!**\n\n"
        "**🔗 Gửi link bất kỳ để rút gọn.**\n"
        "**📷 Chuyển tiếp bài viết kèm ảnh/video, bot sẽ giữ nguyên caption & rút gọn link trong caption.**\n"
        "**💬 Mọi thắc mắc, hãy liên hệ admin.**",
        parse_mode="Markdown"
    )

# Hàm rút gọn link và định dạng text theo yêu cầu
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

# Xử lý tin nhắn nhận được từ Telegram
async def handle_update(update: Update):
    if update.message.media_group_id:
        mgid = update.message.media_group_id
        if mgid not in media_groups:
            media_groups[mgid] = []
            processing_tasks[mgid] = asyncio.create_task(process_media_group(mgid, update.effective_chat.id))
        media_groups[mgid].append(update.message)
        return

    elif update.message.text and update.message.text.startswith("http"):
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

    elif update.message.forward_origin:
        caption = update.message.caption or ""
        new_caption = await format_text(caption)
        await update.message.copy(chat_id=update.effective_chat.id, caption=new_caption, parse_mode="HTML")

# Xử lý media group (nhiều ảnh/video trong cùng một bài)
async def process_media_group(media_group_id: str, user_chat_id: int):
    await asyncio.sleep(random.uniform(3, 5))
    messages = media_groups.pop(media_group_id, [])
    if not messages:
        return
    messages.sort(key=lambda m: m.message_id)
    media = []
    caption = None
    for i, message in enumerate(messages):
        if i == 0 and message.caption:
            caption = await format_text(message.caption)
        if message.photo:
            file_id = message.photo[-1].file_id
            media.append(InputMediaPhoto(media=file_id, caption=caption if i == 0 else None, parse_mode="HTML"))
        elif message.video:
            file_id = message.video.file_id
            media.append(InputMediaVideo(media=file_id, caption=caption if i == 0 else None, parse_mode="HTML"))
    if media:
        await bot.send_media_group(chat_id=user_chat_id, media=media)

# Nếu chạy local, Flask sẽ chạy trên port 5000 (Vercel sẽ sử dụng serverless function tự động)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
