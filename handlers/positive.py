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

# Setup in-memory log handler
def setup_buffer_handler():
    buffer_handler = logging.Handler()
    buffer_handler.emit = lambda record: log_buffer.append(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ).format(record))
    logging.getLogger().addHandler(buffer_handler)

# Schedule first run
def schedule_initial(job_queue):
    delay = random.randint(10, 60)
    job_queue.run_once(random_social_score, when=delay)
    logging.info(f"Initial scoring scheduled in {delay} seconds.")

# Handlers
async def capture_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.chat.type in ['group', 'supergroup'] and msg.text:
        recent_messages.append(msg)
        if len(recent_messages) > 200:
            recent_messages.pop(0)

async def random_social_score(context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if recent_messages:
        msg = random.choice(recent_messages)
        score = random.randint(1, 100)
        uid = msg.from_user.id
        user_scores[uid] += score
        reply = f"+{score} امتیاز اجتماعی 🇮🇷"
        try:
            await context.bot.send_message(chat_id=msg.chat.id, text=reply, reply_to_message_id=msg.message_id)
            logging.info(f"Sent +{score} to {uid}")
        except Exception as e:
            logging.error(f"Send failed: {e}")
    else:
        logging.info('No messages to score.')
    # schedule next
    next_delay = random.randint(10, 60)
    context.job_queue.run_once(random_social_score, when=next_delay)
    logging.info(f"Next run in {next_delay} seconds.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if job_started:
        return
    job_started = True
    setup_buffer_handler()
    await update.message.reply_text("ربات امتیاز اجتماعی فعال شد!")
    # seed
    recent_messages.append(update.effective_message)
    schedule_initial(context.job_queue)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for job in context.job_queue.jobs():
        job.schedule_removal()
    await update.message.reply_text("ربات متوقف شد!")
    logging.info('Jobs cleared.')

async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    total = user_scores.get(uid, 0)
    await update.message.reply_text(f"امتیاز اجتماعی شما: {total} 🇮🇷")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not log_buffer:
        await update.message.reply_text('هیچ لاگی وجود ندارد.')
        return
    lines = list(log_buffer)[-20:]
    text = '```\n' + '\n'.join(lines) + '\n```'
    await update.message.reply_text(text, parse_mode='Markdown')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")
