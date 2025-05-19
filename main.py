import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import json
import os
import time
from config import TOKEN

# Import handlers
from handlers.math import check_answer, start_math_system
from handlers.member import member_handler
from handlers.leaderboard import leaderboard_handler
from handlers.message import message_handler
from handlers.score import score_handler
from handlers.slogan import slogan_handler  # اضافه کردن هندلر جدید

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to track if math system is started in a chat
math_system_started = {}

# Dictionary to track admin warning messages
admin_warnings_sent = {}

# Check if score.json exists, if not create it
if not os.path.exists('score.json'):
    with open('score.json', 'w') as f:
        json.dump({}, f)

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_id = str(update.effective_chat.id)
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        
        if bot_member.status not in ['administrator', 'creator']:
            # Send warning only once every 24 hours (86400 seconds)
            current_time = int(time.time())
            
            if chat_id not in admin_warnings_sent or (current_time - admin_warnings_sent[chat_id]) > 86400:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ <b>توجه:</b> برای کارکرد صحیح ربات، لطفاً آن را به عنوان ادمین گروه اضافه کنید.\n\n"
                         "در غیر این صورت، امکان ثبت عجر وجود ندارد.",
                    parse_mode='HTML'
                )
                admin_warnings_sent[chat_id] = current_time
                logger.info(f"Admin warning sent to chat {chat_id}")
            
            return False
    return True

async def member_handler_wrapper(update, context):
    await member_handler(update, context)

async def leaderboard_handler_wrapper(update, context):
    await leaderboard_handler(update, context)

async def check_answer_wrapper(update, context):
    await check_answer(update, context)

async def score_handler_wrapper(update, context):
    await score_handler(update, context)

async def message_handler_wrapper(update, context):
    chat_id = str(update.effective_chat.id)
    
    # Check admin status first
    is_admin = await check_admin_status(update, context)
    
    # Start math system if not already started in this chat and bot is admin
    if is_admin and chat_id not in math_system_started:
        math_system_started[chat_id] = True
        await start_math_system(update, context)
    
    # Update user activity time
    await update_activity(update, context)
    
    # Process message regardless of admin status
    # (the message_handler itself will check admin status)
    await message_handler(update, context)

def main():
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("leaderboard", leaderboard_handler_wrapper))
    
    # Add the check_answer handler with higher priority
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer_wrapper), group=2)
    
    # Add the message handler with lower priority
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler_wrapper), group=3)

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, member_handler_wrapper), group=4)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, score_handler_wrapper), group=5)
    
    # Add activity update handler in group 6
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, update_activity), group=6)
    
    # Add slogan handler in group 7
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, slogan_handler), group=7)
    
    # Setup inactivity checker
    setup_inactivity_checker(application)
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
