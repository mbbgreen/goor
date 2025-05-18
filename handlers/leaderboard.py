import json
import os
import logging
from telegram.constants import ParseMode

# Configure logging
logger = logging.getLogger(__name__)

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, leaderboard handler not functioning")
            return False
    return True

async def leaderboard_handler(update, context):
    """
    Display the top 10 users with highest points in the group
    """
    # بررسی ادمین بودن ربات
    if not await check_admin_status(update, context):
        return
    
    chat_id = str(update.effective_chat.id)
    
    # Load the score data
    if not os.path.exists('score.json'):
        await update.message.reply_text("هنوز هیچ عجر معنوی ثبت نشده است.")
        logger.info(f"Leaderboard requested in chat {chat_id} but no score file exists")
        return
    
    try:
        with open('score.json', 'r', encoding='utf-8') as f:
            scores = json.load(f)
    except Exception as e:
        logger.error(f"Error loading score file for leaderboard: {e}")
        await update.message.reply_text("خطا در بارگذاری امتیازات. لطفاً بعداً دوباره امتحان کنید.")
        return
    
    # Check if this chat has any scores
    if chat_id not in scores or not scores[chat_id]:
        await update.message.reply_text("هنوز هیچ عجر معنوی در این گروه ثبت نشده است.")
        logger.info(f"Leaderboard requested in chat {chat_id} but no scores exist for this chat")
        return
    
    # Get all users in this chat and sort them by points
    users = []
    for user_id, user_data in scores[chat_id].items():
        users.append({
            'id': user_id,
            'name': user_data.get('name', 'کاربر ناشناس'),
            'points': user_data.get('points', 0),
            'messages': user_data.get('messages', 0)
        })
    
    # Sort users by points (highest first)
    users.sort(key=lambda x: x['points'], reverse=True)
    
    # Get top 10 users
    top_users = users[:10]
    
    # Create leaderboard message
    message = "🇮🇷 <b>لیدربورد عجر معنوی</b> 🇮🇷\n\n"
    
    for i, user in enumerate(top_users, 1):
        # Add medal emoji for top 3
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        message += f"{medal} <b>{user['name']}</b>: {user['points']} عجر معنوی ({user['messages']} پیام)\n"
    
    # Send the leaderboard
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    logger.info(f"Leaderboard sent in chat {chat_id}")
