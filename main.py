import config
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Import handler modules explicitly
from handlers import positive
from handlers import negative
from handlers import leaderboard

# Enable basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    token = getattr(config, 'BOT_TOKEN', None)
    if not token or token.startswith('<'):
        logger.error("Please set BOT_TOKEN in config.py before running.")
        exit(1)

    app = ApplicationBuilder().token(token).build()

    # Positive handlers
    app.add_handler(CommandHandler('start', positive.start))
    app.add_handler(CommandHandler('stop', positive.stop))
    app.add_handler(MessageHandler(filters.Regex(r'امتیاز'), positive.show_score))
    app.add_handler(CommandHandler('logs', positive.show_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, positive.capture_messages))

    # Negative handler
    app.add_handler(CommandHandler('negative', negative.negative_score))

    # Leaderboard handler (triggered by plain text)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^لیست امتیاز$'), leaderboard.show_leaderboard))

    app.add_error_handler(positive.error_handler)

    # Reschedule if already started
    if positive.job_started:
        positive.schedule_initial(app.job_queue)

    logger.info("Bot is running...")
    app.run_polling()
