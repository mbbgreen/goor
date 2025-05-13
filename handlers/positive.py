def positive_module(): pass
import random
import logging
from collections import deque, defaultdict
from telegram import Update
from telegram.ext import ContextTypes

# In-memory buffers
log_buffer = deque(maxlen=100)
user_scores = defaultdict(int)
recent_messages = []
job_started = False

# Logging handler for in-memory logs
def setup_buffer_handler():
    buffer_handler = logging.Handler()
    buffer_handler.emit = lambda record: log_buffer.append(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ).format(record))
    logging.getLogger().addHandler(buffer_handler)

# Scheduler helper
def schedule_initial(job_queue):
    delay = random.randint(10, 60)
    job_queue.run_once(random_social_score, when=delay)
    logging.info(f"Initial scoring scheduled in {delay} seconds.")

# Handler functions
async def capture_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message.chat.type in ['group', 'supergroup'] and message.text:
        recent_messages.append(message)
        if len(recent_messages) > 200:
            recent_messages.pop(0)

async def random_social_score(context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if not recent_messages:
        logging.info('No messages stored yet.')
    else:
        message = random.choice(recent_messages)
        score = random.randint(1, 100)  # updated range 1-100
        user_id = message.from_user.id
        user_scores[user_id] += score
        reply = f"+{score} امتیاز اجتماعی 🇮🇷"
        try:
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=reply,
                reply_to_message_id=message.message_id
            )
            logging.info(f"Sent {score} to {user_id}")
        except Exception as e:
            logging.error(f"Send failed: {e}")
    # schedule next
    delay = random.randint(10, 60)
    context.job_queue.run_once(random_social_score, when=delay)
    logging.info(f"Next run in {delay} seconds.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if job_started:
        return
    job_started = True
    setup_buffer_handler()
    await update.message.reply_text("ربات امتیاز اجتماعی فعال شد!")
    schedule_initial(context.job_queue)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for job in context.job_queue.jobs():
        job.schedule_removal()
    await update.message.reply_text("ربات متوقف شد!")
    logging.info('Stopped and cleared jobs.')

async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    total = user_scores.get(uid, 0)
    await update.message.reply_text(f"امتیاز اجتماعی شما: {total} 🇮🇷")
    logging.info(f"Score for {uid}: {total}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not log_buffer:
        await update.message.reply_text('هیچ لاگی وجود ندارد.')
        return
    lines = list(log_buffer)[-20:]
    text = '```\n' + '\n'.join(lines) + '\n```'
    await update.message.reply_text(text, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} error {context.error}")
