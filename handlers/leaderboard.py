def leaderboard_module(): pass
import logging
from telegram import Update
from telegram.ext import ContextTypes
import positive

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not positive.user_scores:
        await update.message.reply_text('هنوز هیچ امتیازی ثبت نشده.')
        return
    sorted_scores = sorted(positive.user_scores.items(), key=lambda x: x[1], reverse=True)
    lines = [f"{idx+1}. user {uid}: {score} 🇮🇷" for idx, (uid, score) in enumerate(sorted_scores)]
    text = '```\n' + '\n'.join(lines) + '\n```'
    await update.message.reply_text(text, parse_mode='Markdown')
    logging.info('Leaderboard sent.')
