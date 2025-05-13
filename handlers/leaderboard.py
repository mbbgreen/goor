import json
import os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# مسیر فایل امتیازات (در صورت نیاز می‌تونی این مسیر رو تغییر بدی)
SCORES_FILE = "data/scores.json"

# تابع برای خواندن لیست امتیازات از فایل
def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# تابع هندل پیام
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = load_scores()
    if not scores:
        await update.message.reply_text("📭 هنوز هیچ امتیازی ثبت نشده.")
        return

    # مرتب‌سازی امتیازها (بیشترین به کمترین)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "🏆 لیست امتیازات:\n\n"
    for i, (user_id, score) in enumerate(sorted_scores[:10], start=1):
        user_mention = f"<a href='tg://user?id={user_id}'>کاربر {i}</a>"
        leaderboard_text += f"{i}. {user_mention} — {score} امتیاز\n"

    await update.message.reply_text(leaderboard_text, parse_mode="HTML")

# تابع برای برگرداندن هندلر
def get_leaderboard_handler():
    return MessageHandler(filters.Regex(r'^لیست امتیاز$'), show_leaderboard)
