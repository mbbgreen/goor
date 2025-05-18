import json
import os
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to track last message time for each user in each chat
last_message_time = {}

# Minimum time between messages to not be considered spam (in seconds)
MIN_MESSAGE_INTERVAL = 2  # 2 seconds between messages

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, message handler not functioning")
            return False
    return True

async def message_handler(update, context):
    """
    Handle messages and award points for every 100 messages
    Each 100 messages = 15 points
    """
    # بررسی ادمین بودن ربات
    if not await check_admin_status(update, context):
        return
    
    # Get user information
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    chat_id = str(update.effective_chat.id)
    current_time = time.time()
    
    # Check for spam
    if chat_id not in last_message_time:
        last_message_time[chat_id] = {}
    
    # If user has sent a message recently, consider it spam
    if user_id in last_message_time[chat_id]:
        time_since_last_message = current_time - last_message_time[chat_id][user_id]
        if time_since_last_message < MIN_MESSAGE_INTERVAL:
            # This is spam, don't count it
            logger.info(f"Spam detected from user {user_name} ({user_id}) in chat {chat_id}")
            last_message_time[chat_id][user_id] = current_time
            return
    
    # Update last message time
    last_message_time[chat_id][user_id] = current_time
    
    # Check message content
    message_text = update.message.text or ""
    
    # Count words in the message (split by whitespace)
    words = message_text.split()
    word_count = len(words)
    
    # Messages with less than 2 words are considered too short
    if word_count < 2:
        logger.info(f"Message too short (only {word_count} words) from user {user_name} ({user_id}) in chat {chat_id}")
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
    
    # Initialize chat data if not exists
    if chat_id not in scores:
        scores[chat_id] = {}
    
    # Initialize user data if not exists
    if user_id not in scores[chat_id]:
        scores[chat_id][user_id] = {
            "name": user_name,
            "points": 0,
            "messages": 0
        }
    
    # Update user message count
    scores[chat_id][user_id]["messages"] += 1
    scores[chat_id][user_id]["name"] = user_name  # Update name in case it changed
    
    # Check if user reached 100 messages milestone
    if scores[chat_id][user_id]["messages"] % 100 == 0:
        # Award 15 points for every 100 messages
        scores[chat_id][user_id]["points"] += 15
        
        # Notify in the group
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🇮🇷 تبریک {user_name}!\n"
                 f"شما به {scores[chat_id][user_id]['messages']} پیام رسیدید و 15 عجر معنوی دریافت کردید.\n"
                 f"عجر معنوی کل شما: {scores[chat_id][user_id]['points']}"
        )
        
        logger.info(f"User {user_id} reached {scores[chat_id][user_id]['messages']} messages in chat {chat_id} and received 15 points")
    
    # Save updated scores
    try:
        with open('score.json', 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving score file: {e}")
