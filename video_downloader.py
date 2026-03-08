import yt_dlp
import subprocess
import glob
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "7889976375:AAEaq1IMpYwj3n_c7Fhp8aU5yNdjYbR_Slc"

user_links = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a video link (YouTube / Instagram / etc)"
    )


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    link = update.message.text

    if not link.startswith("http"):
        await update.message.reply_text("Please send a valid link.")
        return

    user_links[update.message.chat_id] = link

    keyboard = [
        [InlineKeyboardButton("📥 Download Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data="audio")],
        [InlineKeyboardButton("🖼 Extract Images", callback_data="images")],
    ]

    await update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    link = user_links.get(chat_id)

    if not link:
        await query.message.reply_text("Please send a link first.")
        return

    await query.message.reply_text("Processing...")

    try:

        # download video
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": "video.%(ext)s",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        video_file = glob.glob("video.*")[0]

        # DOWNLOAD VIDEO
        if query.data == "video":

            size = os.path.getsize(video_file) / (1024 * 1024)

            if size > 45:
                await query.message.reply_text(
                    "Video too large for Telegram bot."
                )
                return

            await query.message.reply_video(open(video_file, "rb"))

        # CONVERT AUDIO
        elif query.data == "audio":

            subprocess.run(
                f'ffmpeg -i "{video_file}" audio.mp3',
                shell=True
            )

            await query.message.reply_audio(open("audio.mp3", "rb"))

        # EXTRACT IMAGES
        elif query.data == "images":

            subprocess.run(
                f'ffmpeg -i "{video_file}" -vf fps=1 img_%03d.jpg',
                shell=True
            )

            images = glob.glob("img_*.jpg")

            for img in images[:5]:
                await query.message.reply_photo(open(img, "rb"))

        # cleanup
        for file in glob.glob("video.*"):
            os.remove(file)

        for file in glob.glob("img_*.jpg"):
            os.remove(file)

        if os.path.exists("audio.mp3"):
            os.remove("audio.mp3")

    except Exception as e:
        await query.message.reply_text(f"Error: {str(e)}")


app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .connect_timeout(60)
    .read_timeout(60)
    .write_timeout(120)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot started...")

app.run_polling(drop_pending_updates=True)
