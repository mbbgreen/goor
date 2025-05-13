import random
import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.leaderboard import user_scores, save_scores
from handlers.positive import recent_messages

# متغیر برای کنترل وضعیت کار امتیازدهی منفی
negative_job_started = False

# تابع برای واکنش به دستور منفی (دستی)
async def negative_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not recent_messages:
        await update.message.reply_text("هیچ پیامی برای کم کردن امتیاز نیست.")
        return
    
    msg = random.choice(recent_messages)
    score = random.randint(1, 100)
    uid = str(msg.from_user.id)  # تبدیل به رشته برای اطمینان از سازگاری با JSON
    
    # اگر کاربر امتیازی ندارد، صفر در نظر بگیر
    if uid not in user_scores:
        user_scores[uid] = 0
    
    # اجازه می‌دهیم امتیاز منفی شود
    user_scores[uid] -= score
    reply = f"-{score} امتیاز اجتماعی 🇮🇷 (حال نکردم)"
    
    try:
        await context.bot.send_message(chat_id=msg.chat.id, text=reply, reply_to_message_id=msg.message_id)
        logging.info(f"Subtracted {score} from {uid}")
        # ذخیره امتیازات پس از هر تغییر
        save_scores()
    except Exception as e:
        logging.error(f"Failed negative send: {e}")

    # زمان‌بندی اولیه برای امتیاز منفی
def schedule_initial_negative(job_queue):
    delay = random.randint(150, 1200)  # زمان تصادفی بین 150 تا 1200 ثانیه
    job_queue.run_once(random_negative_score, when=delay)
    logging.info(f"امتیازدهی منفی اولیه در {delay} ثانیه دیگر انجام خواهد شد")

# امتیازدهی منفی تصادفی
async def random_negative_score(context: ContextTypes.DEFAULT_TYPE):
    if recent_messages:
        msg = random.choice(recent_messages)
        score = random.randint(1, 100)
        uid = str(msg.from_user.id)  # تبدیل به رشته برای سازگاری با JSON
        
        # اگر کاربر امتیازی ندارد، صفر در نظر بگیر
        if uid not in user_scores:
            user_scores[uid] = 0
            
        # اجازه می‌دهیم امتیاز منفی شود
        user_scores[uid] -= score
        reply = f"-{score} امتیاز اجتماعی 🇮🇷 (حال نکردم)"
        try:
            await context.bot.send_message(chat_id=msg.chat.id, text=reply, reply_to_message_id=msg.message_id)
            logging.info(f"امتیاز {score}- برای کاربر {uid} کم شد")
            # ذخیره امتیازات پس از هر تغییر
            save_scores()
        except Exception as e:
            logging.error(f"خطا در ارسال امتیاز منفی: {e}")
    else:
        logging.info('هیچ پیامی برای امتیازدهی منفی وجود ندارد')
    
    # زمان‌بندی اجرای بعدی
    next_delay = random.randint(150, 1200)  # زمان تصادفی بین 150 تا 1200 ثانیه
    context.job_queue.run_once(random_negative_score, when=next_delay)
    logging.info(f"اجرای بعدی امتیاز منفی در {next_delay} ثانیه دیگر")

# شروع سیستم امتیاز منفی
async def start_negative(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global negative_job_started
    if negative_job_started:
        await update.message.reply_text("سیستم امتیاز منفی قبلاً فعال شده است!")
        return
    
    negative_job_started = True
    await update.message.reply_text("سیستم امتیاز منفی فعال شد! 🇮🇷")
    
    # شروع زمان‌بندی
    schedule_initial_negative(context.job_queue)

# توقف سیستم امتیاز منفی
async def stop_negative(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global negative_job_started
    if not negative_job_started:
        await update.message.reply_text("سیستم امتیاز منفی فعلاً غیرفعال است!")
        return
    
    # حذف تمام وظایف زمان‌بندی‌شده امتیاز منفی
    for job in context.job_queue.jobs():
        if job.callback == random_negative_score:
            job.schedule_removal()
    
    negative_job_started = False
    await update.message.reply_text("سیستم امتیاز منفی متوقف شد!")
    logging.info('تمام وظایف امتیاز منفی حذف شدند')
