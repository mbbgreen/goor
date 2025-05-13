# handlers/positive.py - ماژول امتیازدهی مثبت

import random
import logging
import json
import os
from collections import deque
from telegram import Update
from telegram.ext import ContextTypes
from handlers.leaderboard import user_scores, save_scores

# متغیرهای سراسری
log_buffer = deque(maxlen=100)
recent_messages = []
job_started = False

# تنظیم هندلر لاگ درون حافظه
def setup_buffer_handler():
    buffer_handler = logging.Handler()
    buffer_handler.emit = lambda record: log_buffer.append(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ).format(record))
    logging.getLogger().addHandler(buffer_handler)
    logging.info("هندلر لاگ تنظیم شد")

# زمان‌بندی اولیه
def schedule_initial(job_queue):
    delay = random.randint(10, 60)
    job_queue.run_once(random_social_score, when=delay)
    logging.info(f"امتیازدهی اولیه در {delay} ثانیه دیگر انجام خواهد شد")

# ثبت پیام‌ها
async def capture_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.chat and msg.chat.type in ['group', 'supergroup'] and msg.text:
        recent_messages.append(msg)
        if len(recent_messages) > 200:
            recent_messages.pop(0)

# امتیازدهی تصادفی
async def random_social_score(context: ContextTypes.DEFAULT_TYPE):
    if recent_messages:
        msg = random.choice(recent_messages)
        score = random.randint(1, 100)
        uid = str(msg.from_user.id)  # تبدیل به رشته برای سازگاری با JSON
        
        # اگر کاربر امتیازی ندارد، صفر در نظر بگیر
        if uid not in user_scores:
            user_scores[uid] = 0
            
        user_scores[uid] += score
        reply = f"+{score} امتیاز اجتماعی 🇮🇷"
        try:
            await context.bot.send_message(chat_id=msg.chat.id, text=reply, reply_to_message_id=msg.message_id)
            logging.info(f"امتیاز {score}+ برای کاربر {uid} ثبت شد")
            # ذخیره امتیازات پس از هر تغییر
            save_scores()
        except Exception as e:
            logging.error(f"خطا در ارسال: {e}")
    else:
        logging.info('هیچ پیامی برای امتیازدهی وجود ندارد')
    
    # زمان‌بندی اجرای بعدی
    next_delay = random.randint(10, 60)
    context.job_queue.run_once(random_social_score, when=next_delay)
    logging.info(f"اجرای بعدی در {next_delay} ثانیه دیگر")

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if job_started:
        await update.message.reply_text("ربات قبلاً فعال شده است!")
        return
    
    job_started = True
    setup_buffer_handler()
    await update.message.reply_text("ربات امتیاز اجتماعی فعال شد! 🇮🇷")
    
    # افزودن پیام فعلی به لیست
    if update.effective_message:
        recent_messages.append(update.effective_message)
    
    # شروع زمان‌بندی
    schedule_initial(context.job_queue)

# توقف ربات
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job_started
    if not job_started:
        await update.message.reply_text("ربات فعلاً غیرفعال است!")
        return
    
    # حذف تمام وظایف زمان‌بندی‌شده
    for job in context.job_queue.jobs():
        job.schedule_removal()
    
    job_started = False
    # ذخیره امتیازات در زمان توقف
    save_scores()
    await update.message.reply_text("ربات متوقف شد!")
    logging.info('تمام وظایف حذف شدند')

# نمایش امتیاز کاربر
async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)  # تبدیل به رشته برای سازگاری با JSON
    total = user_scores.get(uid, 0)
    await update.message.reply_text(f"امتیاز اجتماعی شما: {total} 🇮🇷")

# نمایش لاگ‌ها
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not log_buffer:
        await update.message.reply_text('هیچ لاگی وجود ندارد')
        return
        
    lines = list(log_buffer)[-20:]
    text = '```\n' + '\n'.join(lines) + '\n```'
    await update.message.reply_text(text, parse_mode='Markdown')

# هندلر خطا
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"خطا در بروزرسانی {update}: {context.error}")
