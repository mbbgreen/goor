import random
import logging
import positive
from telegram import Update
from telegram.ext import ContextTypes

async def negative_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # pick a random recent message
    if not positive.recent_messages:
        await update.message.reply_text("هیچ پیامی برای کم کردن امتیاز نیست.")
        return
    message = random.choice(positive.recent_messages)
    score = random.randint(1, 100)
    user_id = message.from_user.id
    # subtract score
    positive.user_scores[user_id] -= score
    reply = f"-{score} امتیاز اجتماعی 🇮🇷 (حال نکردم)"
    try:
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=reply,
            reply_to_message_id=message.message_id
        )
        logging.info(f"Subtracted {score} from {user_id}")
    except Exception as e:
        logging.error(f"Failed to send negative score: {e}")
