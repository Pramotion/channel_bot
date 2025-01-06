from telegram.error import NetworkError, TelegramError
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Constants
BOT_TOKEN = "7866203980:AAHxLFQ0aAbT5NAqjOlBDNJ8dkTVSuruEdI"
CHANNEL_USERNAME = "@betmaster_zone"  # Use channel ID if private, e.g., -1001234567890
stored_content = []  # Store messages, photos, and videos


# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(context.error, NetworkError):
        logger.warning("Network issue occurred. Retrying...")
    elif isinstance(context.error, TelegramError):
        logger.error(f"Telegram API error: {context.error}")
    else:
        logger.error(f"Unexpected error: {context.error}")


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


# Command to manually store messages
async def store_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        message_text = " ".join(context.args)
        stored_content.append({"type": "text", "content": message_text})
        logger.info("Manual message stored successfully.")
        await update.message.reply_text("Message stored successfully!")
    else:
        await update.message.reply_text(
            "Please provide a message to store after the command."
        )


# Command to clear all stored messages
async def restore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stored_content
    stored_content.clear()
    logger.info("All stored messages cleared.")
    await update.message.reply_text("All stored messages have been removed.")


# Function to send all messages to the channel
async def send_to_channel(bot: Bot):
    global stored_content

    if not stored_content:
        logger.info("No content to send.")
        return

    for item in stored_content:
        try:
            if item["type"] == "photo":
                await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=item["content"])
            elif item["type"] == "video":
                await bot.send_video(chat_id=CHANNEL_USERNAME, video=item["content"])
            elif item["type"] == "text":
                await bot.send_message(chat_id=CHANNEL_USERNAME, text=item["content"])
            logger.info(f"Sent {item['type']} to the channel: {item['content']}")
        except Exception as e:
            logger.error(f"Error sending {item['type']}: {e}")


# Scheduler setup
def schedule_jobs(application):
    scheduler = AsyncIOScheduler()

    async def send_job():
        logger.info("Scheduled send job triggered.")
        try:
            await send_to_channel(application.bot)  # Pass the bot directly
        except Exception as e:
            logger.error(f"Error during scheduled job: {e}")

    scheduler.add_job(
        send_job,
        IntervalTrigger(minutes=1),  # Adjust the interval as needed
    )
    scheduler.start()
    logger.info("Jobs scheduled successfully.")


# Main function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.ALL, store_message))
    application.add_handler(CommandHandler("store", store_command))
    application.add_handler(CommandHandler("restore", restore_command))

    # Schedule jobs
    schedule_jobs(application)

    # Run the bot
    logger.info("Bot is running.")
    application.run_polling()


if __name__ == "__main__":
    main()
