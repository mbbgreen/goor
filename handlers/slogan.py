import json
import os
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to track last slogan time for each user in each chat
last_slogan_time = {}

# List of accepted slogans
ACCEPTED_SLOGANS = [
    "درود بر جمهوری اسلامی ایران",
    "درود بر سید علی خامنه ای",
    "درود بر سپاه پاسداران",
    "درود بر سپاه پاسداران انقلاب اسلامی"
]

# Time interval between slogans (5 minutes = 300 seconds)
SLOGAN_INTERVAL = 300

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, slogan handler not functioning")
            return False
    return True

async def slogan_handler(update, context):
    """Handle slogan messages and award points"""
    # Check if bot is admin
    if not await check_admin_status(update, context):
        return
    
    message_text = update.message.text.strip()
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    current_time = time.time()
    
    # Check if the message is one of the accepted slogans
    if message_text not in ACCEPTED_SLOGANS:
        # Check if message contains emoji but text matches
        for slogan in ACCEPTED_SLOGANS:
            if slogan in message_text:
                # Extract the part that matches the slogan
                if message_text.replace("🇮🇷", "").strip() == slogan:
                    message_text = slogan
                    break
    
    if message_text not in ACCEPTED_SLOGANS:
        return
    
    # Initialize chat data if not exists
    if chat_id not in last_slogan_time:
        last_slogan_time[chat_id] = {}
    
    # Check if user can post a slogan (5 minutes cooldown)
    if user_id in last_slogan_time[chat_id]:
        time_since_last = current_time - last_slogan_time[chat_id][user_id]
        if time_since_last < SLOGAN_INTERVAL:
            # کاربر هنوز باید صبر کند، اما پیامی نمایش داده نمی‌شود
            logger.info(f"User {user_id} in chat {chat_id} tried to post slogan too soon")
            return
    
    # Update last slogan time
    last_slogan_time[chat_id][user_id] = current_time
    
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
    
    # Initialize chat and user if not exists
    if chat_id not in scores:
        scores[chat_id] = {}
    if user_id not in scores[chat_id]:
        scores[chat_id][user_id] = {
            "name": user_name,
            "points": 0,
            "messages": 0
        }
    
    # Award 1 point
    scores[chat_id][user_id]["points"] += 1
    
    # Save updated scores
    with open('score.json', 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)
    
    # Send confirmation message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🇮🇷 {user_name}، بابت شعار انقلابی شما 1 عجر معنوی دریافت کردید!\n"
             f"عجر معنوی فعلی: {scores[chat_id][user_id]['points']}"
    )
    logger.info(f"User {user_id} in chat {chat_id} awarded 1 point for slogan")
