import json
import os
import random
import time
import logging
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, filters

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to track active math challenges
active_challenges = {}

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, math handler not functioning")
            return False
    return True

def generate_math_problem():
    """Generate a random math problem with numbers between 1-100"""
    operations = ['+', '-', '*', '/']
    operation = random.choice(operations)
    
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    
    # Ensure division results in a whole number
    if operation == '/':
        num1 = num2 * random.randint(1, 10)
    
    # Calculate the answer
    if operation == '+':
        answer = num1 + num2
    elif operation == '-':
        answer = num1 - num2
    elif operation == '*':
        answer = num1 * num2
    else:  # operation == '/'
        answer = num1 // num2
    
    problem = f"{num1} {operation} {num2}"
    return problem, answer

async def delete_challenge_message(context, chat_id, message_id):
    """Delete the challenge message after a delay"""
    try:
        await context.bot.delete_message(chat_id=int(chat_id), message_id=message_id)
        logger.info(f"Deleted challenge message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Error deleting challenge message: {e}")

async def check_answer(update, context):
    """Check if the answer provided by the user is correct"""
    # بررسی ادمین بودن ربات
    if not await check_admin_status(update, context):
        return
    
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # Check if there's an active challenge in this chat
    if chat_id not in active_challenges:
        return
    
    # Get the expected answer and other challenge details
    expected_answer = active_challenges[chat_id]["answer"]
    message_id = active_challenges[chat_id]["message_id"]
    problem = active_challenges[chat_id]["problem"]
    
    # Try to parse the user's answer
    try:
        user_answer = int(update.message.text.strip())
    except ValueError:
        return  # Not a number, ignore
    
    # Check if the answer is correct
    if user_answer == expected_answer:
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
        
        # Award 5 points for correct answer
        scores[chat_id][user_id]["points"] += 5
        scores[chat_id][user_id]["name"] = user_name  # Update name in case it changed
        
        # Edit the original challenge message instead of sending a new one
        await context.bot.edit_message_text(
            chat_id=int(chat_id),
            message_id=message_id,
            text=f"🧮 <b>چالش ریاضی!</b> 🧮\n\n"
                 f"<code>{problem} = {expected_answer}</code>\n\n"
                 f"🇮🇷 <b>{user_name}</b> پاسخ درست داد!\n"
                 f"5 عجر معنوی به ایشان اضافه شد.\n"
                 f"عجر معنوی کل: {scores[chat_id][user_id]['points']}",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"User {user_id} correctly answered math challenge in chat {chat_id} and received 5 points")
        
        # Save updated scores
        try:
            with open('score.json', 'w', encoding='utf-8') as f:
                json.dump(scores, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving score file: {e}")
        
        # Remove the challenge as it's been solved
        del active_challenges[chat_id]
        
        # Schedule message deletion after 30 seconds
        context.job_queue.run_once(
            lambda ctx: delete_challenge_message(ctx, chat_id, message_id),
            30
        )
        
        # Schedule the next challenge
        await schedule_next_challenge(context, chat_id)

async def challenge_timeout(context):
    """Handle timeout for a math challenge"""
    job = context.job
    chat_id = job.data
    
    if chat_id in active_challenges:
        problem = active_challenges[chat_id]["problem"]
        answer = active_challenges[chat_id]["answer"]
        message_id = active_challenges[chat_id]["message_id"]
        
        # Remove the challenge
        del active_challenges[chat_id]
        
        # Edit the original message instead of sending a new one
        await context.bot.edit_message_text(
            chat_id=int(chat_id),
            message_id=message_id,
            text=f"🧮 <b>چالش ریاضی!</b> 🧮\n\n"
                 f"<code>{problem} = {answer}</code>\n\n"
                 f"⏰ <b>زمان به پایان رسید!</b>\n"
                 f"هیچکس به سوال پاسخ نداد.",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Math challenge timed out in chat {chat_id}")
        
        # Schedule message deletion after 30 seconds
        context.job_queue.run_once(
            lambda ctx: delete_challenge_message(ctx, chat_id, message_id),
            30
        )
        
        # Schedule the next challenge
        await schedule_next_challenge(context, chat_id)

async def send_challenge(context):
    """Send a math challenge to the specified chat"""
    # Get chat_id from job data
    job = context.job
    chat_id = job.data
    
    try:
        # Check if bot is admin in the chat
        try:
            bot_member = await context.bot.get_chat_member(int(chat_id), context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                logger.warning(f"Bot is not admin in chat {chat_id}, skipping math challenge")
                return
        except Exception as e:
            logger.error(f"Error checking admin status in chat {chat_id}: {e}")
            return
        
        # Generate a new math problem
        problem, answer = generate_math_problem()
        
        # Send the challenge
        message = await context.bot.send_message(
            chat_id=int(chat_id),
            text=f"🧮 <b>چالش ریاضی!</b> 🧮\n\n"
                 f"اولین کسی باشید که به این سوال پاسخ میدهد:\n\n"
                 f"<code>{problem} = ?</code>\n\n"
                 f"(5 عجر معنوی برای پاسخ صحیح)\n"
                 f"⏰ زمان: 90 ثانیه",
            parse_mode=ParseMode.HTML
        )
        
        # Store the challenge details
        active_challenges[chat_id] = {
            "problem": problem,
            "answer": answer,
            "timestamp": time.time(),
            "message_id": message.message_id
        }
        
        logger.info(f"Math challenge sent to chat {chat_id}: {problem} = {answer}")
        
        # Set a timeout for this challenge (90 seconds)
        context.job_queue.run_once(challenge_timeout, 90, data=chat_id)
    except Exception as e:
        logger.error(f"Error sending math challenge to chat {chat_id}: {e}")

async def schedule_next_challenge(context, chat_id):
    """Schedule the next math challenge"""
    # Random time between 3-25 minutes (180-1500 seconds)
    delay = random.randint(180, 1500)
    
    # Log the next challenge time but don't send a message to the chat
    logger.info(f"Next math challenge for chat {chat_id} scheduled in {delay} seconds")
    
    # Schedule the next challenge
    context.job_queue.run_once(send_challenge, delay, data=chat_id)

async def start_math_system(update, context):
    """Start the math challenge system in the group"""
    # بررسی ادمین بودن ربات
    if not await check_admin_status(update, context):
        return
    
    chat_id = str(update.effective_chat.id)
    
    # Check if math challenges are already running in this chat
    if chat_id in active_challenges:
        return
    
    logger.info(f"Math challenge system activated in chat {chat_id}")
    
    # Schedule the first challenge
    await schedule_next_challenge(context, chat_id)
