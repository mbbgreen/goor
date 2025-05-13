# main.py
# Entry point: registers handlers and starts the bot
import config
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Import handler modules explicitly
import handlers.positive as positive
import handlers.negative as negative
import handlers.leaderboard as leaderboard
from handlers.leaderboard import get_leaderboard_handler

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
    app.add_handler(CommandHandler('start', positive.start, group=0))
    app.add_handler(CommandHandler('stop', positive.stop, group=1))
    # show user score only on exact "امتیاز"
    app.add_handler(MessageHandler(filters.Regex(r'^امتیاز$'), positive.show_score, group=2))
    app.add_handler(CommandHandler('logs', positive.show_logs, group=2))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, positive.capture_messages, group=2))

    # Negative handler
    app.add_handler(CommandHandler('negative', negative.negative_score, group=3))

    # Leaderboard handler (triggered by plain text)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^لیست امتیاز$'), leaderboard.show_leaderboard, group=4))

    app.add_handler(get_leaderboard_handler(), group=4)

    app.add_error_handler(positive.error_handler)

    # Reschedule if already started
    if positive.job_started:
        positive.schedule_initial(app.job_queue)

    logger.info("Bot is running...")
    app.run_polling()
