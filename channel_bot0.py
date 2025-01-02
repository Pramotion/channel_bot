import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
BOT_TOKEN = '8019314390:AAG3yq_xEUd_ofBPqOcPRk5jWMZKZzmpKlQ'
CHANNEL_USERNAME = '@gameannouncement'
stored_content = []  # Store messages, photos, and videos

# Handler to store incoming messages
async def store_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        stored_content.append({"type": "photo", "content": photo})
        logger.info("Photo stored successfully.")
        await update.message.reply_text("Photo stored successfully!")
    elif update.message.video:
        video = update.message.video.file_id
        stored_content.append({"type": "video", "content": video})
        logger.info("Video stored successfully.")
        await update.message.reply_text("Video stored successfully!")
    elif update.message.text:
        text = update.message.text
        stored_content.append({"type": "text", "content": text})
        logger.info("Text message stored successfully.")
        await update.message.reply_text("Message stored successfully!")
    else:
        await update.message.reply_text("Unsupported content type.")

# Function to send all messages to the channel
async def send_to_channel(context: ContextTypes.DEFAULT_TYPE):
    if not stored_content:
        logger.info("No content to send.")
        return

    for item in stored_content[:]:  # Iterate over a copy to allow modification
        try:
            if item["type"] == "photo":
                await context.bot.send_photo(chat_id=CHANNEL_USERNAME, photo=item["content"])
            elif item["type"] == "video":
                await context.bot.send_video(chat_id=CHANNEL_USERNAME, video=item["content"])
            elif item["type"] == "text":
                await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=item["content"])
            logger.info(f"Sent {item['type']} to the channel.")
            stored_content.remove(item)  # Remove after successfully sending
        except Exception as e:
            logger.error(f"Error sending content: {e}")

# Scheduler setup
def schedule_jobs(application):
    scheduler = AsyncIOScheduler()

    async def send_job():
        # Use the bot context to call send_to_channel
        bot_context = ContextTypes.DEFAULT_TYPE(application.bot)
        await send_to_channel(bot_context)

    scheduler.add_job(
        send_job, 
        IntervalTrigger(minutes=30),  # Send every 30 minutes
    )
    scheduler.start()
    logger.info("Jobs scheduled successfully.")

# Main function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.ALL, store_message))

    # Schedule jobs
    schedule_jobs(application)

    # Run the bot
    logger.info("Bot is running.")
    application.run_polling()

if __name__ == "__main__":
    main()
