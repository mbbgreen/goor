import json
import os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# مسیر فایل امتیازات
SCORES_FILE = "data/scores.json"

# دیکشنری برای نگهداری امتیازات کاربران
user_scores = {}

# تابع برای خواندن لیست امتیازات از فایل
def load_scores():
    global user_scores
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                user_scores = json.load(f)
                return user_scores
        except Exception as e:
            print(f"خطا در خواندن فایل امتیازات: {e}")
            return {}
    
    # اطمینان از وجود پوشه data
    os.makedirs(os.path.dirname(SCORES_FILE), exist_ok=True)
    return {}

# تابع برای ذخیره امتیازات در فایل
def save_scores():
    try:
        # اطمینان از وجود پوشه data
        os.makedirs(os.path.dirname(SCORES_FILE), exist_ok=True)
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(user_scores, f, ensure_ascii=False)
    except Exception as e:
        print(f"خطا در ذخیره‌سازی امتیازات: {e}")

# تابع برای دریافت اطلاعات کاربر با استفاده از شناسه کاربر
async def get_user_info(bot, user_id):
    try:
        chat_member = await bot.get_chat_member(chat_id=user_id, user_id=user_id)
        user = chat_member.user
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name if user.last_name else "",
            'username': user.username if user.username else ""
        }
    except Exception as e:
        print(f"خطا در دریافت اطلاعات کاربر {user_id}: {e}")
        return None

# تابع هندل پیام
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_scores:
        await update.message.reply_text("📭 هنوز هیچ امتیازی ثبت نشده.")
        return

    # مرتب‌سازی امتیازها (بیشترین به کمترین)
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "🏆 لیست امتیازات:\n\n"
    
    # حداکثر 10 نفر از لیست را نمایش می‌دهیم
    top_users = sorted_scores[:10]
    
    for i, (user_id, score) in enumerate(top_users, start=1):
        try:
            # دریافت اطلاعات کاربر از تلگرام
            chat = await context.bot.get_chat(user_id)
            user_name = chat.first_name
            if chat.last_name:
                user_name += f" {chat.last_name}"
            if chat.username:
                user_mention = f"<a href='tg://user?id={user_id}'>{user_name} (@{chat.username})</a>"
            else:
                user_mention = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
                
        except Exception as e:
            # اگر نتوانستیم اطلاعات کاربر را دریافت کنیم، از یک نام عمومی استفاده می‌کنیم
            print(f"خطا در دریافت اطلاعات کاربر: {e}")
            user_mention = f"<a href='tg://user?id={user_id}'>کاربر {user_id}</a>"
            
        leaderboard_text += f"{i}. {user_mention} — {score} امتیاز\n"

    await update.message.reply_text(leaderboard_text, parse_mode="HTML")

# تابع برای برگرداندن هندلر
def get_leaderboard_handler():
    return MessageHandler(filters.Regex(r'^لیست امتیاز$'), show_leaderboard)
