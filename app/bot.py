import logging
import asyncio
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to store user decision
user_decision = None
confirmation_event = asyncio.Event()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tatort Bot is running. Waiting for jobs.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_decision
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "post":
        user_decision = True
        await query.edit_message_caption(caption="Confirmed! Posting to social media...")
    elif data == "discard":
        user_decision = False
        await query.edit_message_caption(caption="Discarded. No post will be made.")
        
    confirmation_event.set()

async def send_confirmation_async(token, chat_id, video_path, stats_text):
    global user_decision
    user_decision = None
    confirmation_event.clear()
    
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Send video and stats
    logging.info("Sending video to Telegram...")
    try:
        # Check if video exists
        if not os.path.exists(video_path):
            logging.error(f"Video file not found: {video_path}")
            return False

        keyboard = [
            [
                InlineKeyboardButton("Post", callback_data="post"),
                InlineKeyboardButton("Discard", callback_data="discard"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        async with application.bot:
            await application.bot.send_video(
                chat_id=chat_id,
                video=open(video_path, 'rb'),
                caption=f"New Tatort Processed!\n\n{stats_text}\n\nDo you want to post this?",
                reply_markup=reply_markup,
                read_timeout=60, 
                write_timeout=60, 
                connect_timeout=60
            )
            
            logging.info("Message sent. Waiting for response...")
            
            # We need to run the application to receive updates
            # Since we are in a script, we can start polling, wait for event, then stop.
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            # Wait for decision
            await confirmation_event.wait()
            
            # Stop
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            
            return user_decision
            
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return False

def request_confirmation(video_path, stats_text):
    """
    Synchronous wrapper to request confirmation via Telegram.
    Blocks until user responds.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logging.error("Telegram credentials missing (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).")
        return False
        
    try:
        return asyncio.run(send_confirmation_async(token, chat_id, video_path, stats_text))
    except Exception as e:
        logging.error(f"Failed to run async telegram task: {e}")
        return False

if __name__ == "__main__":
    # Test run
    # Create a dummy file for testing
    dummy_video = "test_video.mp4"
    with open(dummy_video, "wb") as f:
        f.write(b"dummy")
        
    # Set env vars for testing if needed, or assume they are set
    # os.environ["TELEGRAM_BOT_TOKEN"] = "..."
    # os.environ["TELEGRAM_CHAT_ID"] = "..."
    
    print("Sending test confirmation...")
    # result = request_confirmation(dummy_video, "Stats: 5 scenes found.")
    # print(f"Result: {result}")
    
    # Clean up
    if os.path.exists(dummy_video):
        os.remove(dummy_video)
