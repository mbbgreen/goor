import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.positive import user_scores

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_scores:
        await update.message.reply_text('هنوز هیچ امتیازی ثبت نشده.')
        return
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    lines = [f"{i+1}. کاربر {uid}: {score} 🇮🇷" for i, (uid, score) in enumerate(sorted_scores)]
    text = '```\n' + '\n'.join(lines) + '\n```'
    await update.message.reply_text(text, parse_mode='Markdown')
    logging.info('Leaderboard sent.')
