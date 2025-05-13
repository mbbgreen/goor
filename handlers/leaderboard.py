from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from database import load_scores  # فرض بر اینه که امتیازات تو دیتابیس ذخیره‌ان

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = load_scores()
    if not scores:
        await update.message.reply_text("هیچ امتیازی ثبت نشده.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 رتبه‌بندی کاربران:\n"
    for i, (user_id, score) in enumerate(sorted_scores, start=1):
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        username = member.user.full_name
        text += f"{i}. {username} - {score} امتیاز\n"

    await update.message.reply_text(text)

# هندلر مربوطه:
leaderboard_text_handler = MessageHandler(
    filters.TEXT & filters.Regex(r"^لیست امتیاز$"),
    leaderboard_handler
)
