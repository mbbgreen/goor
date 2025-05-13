import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Import handler modules explicitly
import handlers.positive as positive
import handlers.negative as negative
import handlers.leaderboard as leaderboard
import config  # فرض بر اینه config.py موجوده

# Enable basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main():
    # بررسی وجود توکن
    token = getattr(config, 'BOT_TOKEN', None)
    if not token or token.startswith('<'):
        logger.error("لطفاً BOT_TOKEN را در فایل config.py تنظیم کنید.")
        exit(1)
    
    # ساخت اپلیکیشن
    app = ApplicationBuilder().token(token).build()
    
    # بارگذاری امتیازات قبلی
    leaderboard.load_scores()
    
    # ثبت هندلرهای مثبت
    app.add_handler(CommandHandler('start', positive.start), group=0)
    app.add_handler(CommandHandler('stop', positive.stop), group=1)
    app.add_handler(MessageHandler(filters.Regex(r'^امتیاز$'), positive.show_score), group=2)
    app.add_handler(CommandHandler('logs', positive.show_logs), group=2)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, positive.capture_messages), group=2)
    
    # ثبت هندلر منفی
    app.add_handler(MessageHandler(filters.Regex(r'^منفی$'), negative.negative_score), group=3)
    app.add_handler(CommandHandler('start_negative', negative.start_negative), group=3)
    app.add_handler(CommandHandler('stop_negative', negative.stop_negative), group=3)
    
    # ثبت هندلرهای لیدربورد
    app.add_handler(MessageHandler(filters.Regex(r'^لیست امتیاز$'), leaderboard.show_leaderboard), group=4)
    
    # ثبت هندلر خطا
    app.add_error_handler(positive.error_handler)
    
    # برنامه‌ریزی مجدد اگر قبلاً شروع شده باشد
    if positive.job_started:
        positive.schedule_initial(app.job_queue)
    
    # برنامه‌ریزی مجدد برای امتیاز منفی اگر فعال شده باشد
    if hasattr(negative, 'negative_job_started') and negative.negative_job_started:
        negative.schedule_initial_negative(app.job_queue)
    
    logger.info("ربات در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
