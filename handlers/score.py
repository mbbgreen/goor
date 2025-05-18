import json
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to track if welcome message has been sent in a chat
welcome_sent = {}

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, score handler not functioning")
            return False
    return True

async def score_handler(update, context):
    """
    Handle the 'عجر' command to show user's score
    Also sends welcome message on first message in a chat
    """
    # Check if bot is admin
    if not await check_admin_status(update, context):
        return
    
    message_text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # Check if this is the first message in the chat
    if chat_id not in welcome_sent:
        welcome_sent[chat_id] = True
        
        # Send welcome message with available commands - for the group, not specific to user
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👋 <b>سلام به همگی!</b>\n\n"
                 f"علی خامنه ای در این گروه فعال شد🇮🇷.\n"
                 f"شما با چالش هایی که برایتان فرا میخوانیم میتوانید اجر معنوی به دست بی آورید.\n\n"      
                 f"🔹 <b>دستورات موجود:</b>\n"
                 f"• نوشتن <code>عجر</code> برای مشاهده عجر معنوی خود\n"
                 f"• <code>/leaderboard</code> برای مشاهده جدول \n\n"
                 f"🔸 <b>روش‌های کسب عجر معنوی:</b>\n"
                 f"• پاسخ صحیح به چالش‌های ریاضی: 5 عجر معنوی\n"
                 f"• ارسال هر 100 پیام(اسپم روا نیست): 15 عجر معنوی\n"
                 f"• اضافه کردن هر عضو جدید: 25 عجر معنوی\n"
                 f"• ارسال شعارهای انقلابی هر 5 دقیقه: 1 عجر معنوی\n\n"
                 f"چالش‌های ریاضی به صورت خودکار در گروه ارسال می‌شوند. موفق باشید! 🎯",
            parse_mode='HTML'
        )
        logger.info(f"Welcome message sent to chat {chat_id}")
    
    # Check if the message is exactly 'عجر'
    if message_text != "عجر":
        return
    
    # Load the score data
    try:
        if os.path.exists('score.json'):
            with open('score.json', 'r', encoding='utf-8') as f:
                scores = json.load(f)
        else:
            scores = {}
    except Exception as e:
        logger.error(f"Error loading score file: {e}")
        scores = {}
    
    # Get user's score
    if chat_id in scores and user_id in scores[chat_id]:
        user_score = scores[chat_id][user_id]["points"]
        messages_count = scores[chat_id][user_id]["messages"]
    else:
        user_score = 0
        messages_count = 0
    
    # Send the score information
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🇮🇷 <b>اطلاعات عجر معنوی {user_name}:</b>\n\n"
             f"• عجر کل: <b>{user_score}</b>\n"
             f"• تعداد پیام‌ها: {messages_count}\n\n"
             f"برای مشاهده جدول از دستور /leaderboard استفاده کنید.",
        parse_mode='HTML'
    )
    logger.info(f"Score information sent to user {user_id} in chat {chat_id}")
