# main.py
# Entry point: registers handlers and starts the bot
import sys
import os
# Ensure current directory is in module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import positive
import negative
import leaderboard

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

    # Positive module handlers
    app.add_handler(CommandHandler('start', positive.start))
    app.add_handler(CommandHandler('stop', positive.stop))
    app.add_handler(MessageHandler(filters.Regex(r'امتیاز'), positive.show_score))
    app.add_handler(CommandHandler('logs', positive.show_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, positive.capture_messages))

    # Negative scoring handler
    app.add_handler(CommandHandler('negative', negative.negative_score))

    # Leaderboard handler
    app.add_handler(CommandHandler('leaderboard', leaderboard.show_leaderboard))

    app.add_error_handler(positive.error_handler)

    # Trigger initial scheduling if already started
    if positive.job_started:
        positive.schedule_initial(app.job_queue)

    app.run_polling()
