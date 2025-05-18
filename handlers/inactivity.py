import json
import os
import logging
import time
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to track last activity time for each user in each chat
last_activity_time = {}

# Dictionary to track inactivity notifications
inactivity_notifications = {}

# زمان‌های واقعی
SECONDS_PER_HOUR = 3600  # هر 3600 ثانیه = 1 ساعت
NOTIFICATION_HOURS = 5    # تعداد ساعت‌های غیرفعالی برای اعلان

async def check_admin_status(context, chat_id):
    """Check if the bot is admin in the group"""
    try:
        bot_member = await context.bot.get_chat_member(int(chat_id), context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {chat_id}, inactivity handler not functioning")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking admin status in chat {chat_id}: {e}")
        return False

async def update_activity(update, context):
    """Update the last activity time for a user"""
    # Get user information
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    current_time = time.time()
    
    # Initialize chat data if not exists
    if chat_id not in last_activity_time:
        last_activity_time[chat_id] = {}
    
    # Update last activity time
    last_activity_time[chat_id][user_id] = current_time
    
    # Reset inactivity notification counter if exists
    if chat_id in inactivity_notifications and user_id in inactivity_notifications[chat_id]:
        inactivity_notifications[chat_id][user_id] = 0

    logger.info(f"Updated activity time for user {user_id} in chat {chat_id}")

async def check_inactivity(context):
    """Check for inactive users and deduct points"""
    current_time = time.time()
    
    try:
        # Load the score data
        if os.path.exists('score.json'):
            with open('score.json', 'r', encoding='utf-8') as f:
                scores = json.load(f)
        else:
            scores = {}
            
        # Initialize inactivity notifications dictionary if not exists
        if not inactivity_notifications:
            for chat_id in last_activity_time:
                inactivity_notifications[chat_id] = {}
        
        # Check each chat
        for chat_id in list(last_activity_time.keys()):
            # Skip if chat is not in scores
            if chat_id not in scores:
                continue
                
            # Check if bot is admin in this chat
            is_admin = await check_admin_status(context, chat_id)
            if not is_admin:
                logger.info(f"Skipping inactivity check for chat {chat_id} as bot is not admin")
                continue
                
            # Check each user in the chat
            for user_id, last_time in list(last_activity_time[chat_id].items()):
                if user_id not in scores[chat_id]:
                    continue
                    
                # Calculate hours of inactivity
                seconds_inactive = current_time - last_time
                hours_inactive = int(seconds_inactive / SECONDS_PER_HOUR)
                
                logger.info(f"User {user_id} in chat {chat_id} has been inactive for {seconds_inactive} seconds ({hours_inactive} hours)")
                
                # If inactive for at least 1 hour
                if hours_inactive >= 1:
                    # Initialize inactivity counter if not exists
                    if chat_id not in inactivity_notifications:
                        inactivity_notifications[chat_id] = {}
                    if user_id not in inactivity_notifications[chat_id]:
                        inactivity_notifications[chat_id][user_id] = 0
                    
                    # Calculate how many new hours to deduct points for
                    new_hours = hours_inactive - inactivity_notifications[chat_id][user_id]
                    
                    if new_hours > 0:
                        # Deduct 1 point per hour
                        points_to_deduct = min(new_hours, scores[chat_id][user_id]["points"])  # Don't go below 0
                        if points_to_deduct > 0:
                            scores[chat_id][user_id]["points"] -= points_to_deduct
                            
                            # Update the notification counter
                            inactivity_notifications[chat_id][user_id] = hours_inactive
                            
                            logger.info(f"Deducted {points_to_deduct} points from user {scores[chat_id][user_id]['name']} ({user_id}) in chat {chat_id} for {new_hours} hours of inactivity")
                        
                        # If reached notification threshold hours of inactivity, send notification
                        if hours_inactive == NOTIFICATION_HOURS:
                            try:
                                await context.bot.send_message(
                                    chat_id=int(chat_id),
                                    text=f"👎 {scores[chat_id][user_id]['name']} به مدت {NOTIFICATION_HOURS} ساعت فعالیتی نداشته!\n"
                                         f"-{NOTIFICATION_HOURS} عجر معنوی (فعالیت نداری حال نکردم)\n"
                                         f"عجر معنوی فعلی: {scores[chat_id][user_id]['points']}"
                                )
                                logger.info(f"Sent inactivity notification for user {user_id} in chat {chat_id}")
                            except Exception as e:
                                logger.error(f"Error sending inactivity notification: {e}")
        
        # Save updated scores
        with open('score.json', 'w', encoding='utf-8') as f:
            json.dump(scores, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        logger.error(f"Error in check_inactivity: {e}")

def setup_inactivity_checker(application):
    """Setup the inactivity checker job"""
    # بررسی هر ساعت یکبار
    application.job_queue.run_repeating(check_inactivity, interval=3600, first=3600)
    logger.info("Inactivity checker job scheduled")
