# main.py
import os
import random
import logging
import config  # config.py should define BOT_TOKEN = '<your-token-here>'

from collections import deque, defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Enable logging with in-memory buffer
log_buffer = deque(maxlen=100)
class BufferHandler(logging.Handler):
    def emit(self, record):
        log_buffer.append(self.format(record))

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
buffer_handler = BufferHandler()
buffer_handler.setFormatter(formatter)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.addHandler(buffer_handler)

# Store recent messages and user scores
ecent_messages = []
MAX_MESSAGES = 200  # Max stored messages
user_scores = defaultdict(int)  # accumulate scores per user_id

async def capture_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message.chat.type in ['group', 'supergroup'] and message.text:
        recent_messages.append(message)
        if len(recent_messages) > MAX_MESSAGES:
            recent_messages.pop(0)

async def random_social_score(context: ContextTypes.DEFAULT_TYPE):
    if not recent_messages:
        logger.info('No messages stored yet.')
    else:
        message = random.choice(recent_messages)
        score = random.randint(1, 10000)
        user_id = message.from_user.id
        user_scores[user_id] += score
        reply_text = f"+{score} امتیاز اجتماعی 🇮🇷"
        try:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=reply_text,
                reply_to_message_id=message.message_id,
            )
            logger.info(f"Sent score {score} to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    # schedule next random run between 1 and 15 minutes
    next_delay = random.randint(60, 900)
    context.job_queue.run_once(random_social_score, when=next_delay)
    logger.info(f"Next score scheduled in {next_delay} seconds.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات امتیاز اجتماعی فعال شد!")
    # schedule first run
    initial_delay = random.randint(10, 600)
    context.job_queue.run_once(random_social_score, when=initial_delay)
    logger.info(f'Bot started; first run in {initial_delay} seconds.')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for job in context.job_queue.jobs():
        job.schedule_removal()
    await update.message.reply_text("ربات امتیاز اجتماعی متوقف شد!")
    logger.info('Bot stopped and jobs removed.')

async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    total = user_scores.get(user.id, 0)
    text = f"امتیاز اجتماعی شما: {total} 🇮🇷"
    await update.message.reply_text(text)
    logger.info(f"Score shown for {user.id}: {total}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not log_buffer:
        await update.message.reply_text('هیچ لاگی وجود ندارد.')
        return
    logs = list(log_buffer)[-20:]
    text = "```
" + "
".join(logs) + "
```"
    await update.message.reply_text(text, parse_mode='Markdown')
    logger.info('Logs sent to user.')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    token = getattr(config, 'BOT_TOKEN', None)
    if not token or token.startswith('<'):
        logger.error("Please set BOT_TOKEN in config.py before running.")
        exit(1)

    application = ApplicationBuilder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('logs', show_logs))
    # show score when user types "امتیاز"
    application.add_handler(MessageHandler(filters.Regex(r'امتیاز'), show_score))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, capture_messages)
    )
    application.add_error_handler(error_handler)

    application.run_polling()

# config.py (new file)
# --------------------
# BOT_TOKEN = '123456789:ABCdefGhIjklMNopQRsTUVwxyz'
