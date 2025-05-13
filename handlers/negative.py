import random
import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.positive import recent_messages, user_scores

async def negative_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not recent_messages:
        await update.message.reply_text("هیچ پیامی برای کم کردن امتیاز نیست.")
        return
    msg = random.choice(recent_messages)
    score = random.randint(1, 100)
    uid = msg.from_user.id
    user_scores[uid] -= score
    reply = f"-{score} امتیاز اجتماعی 🇮🇷 (حال نکردم)"
    try:
        await context.bot.send_message(chat_id=msg.chat.id, text=reply, reply_to_message_id=msg.message_id)
        logging.info(f"Subtracted {score} from {uid}")
    except Exception as e:
        logging.error(f"Failed negative send: {e}")
