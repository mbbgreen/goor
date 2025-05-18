import json
import os
import logging
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

async def check_admin_status(update, context):
    """Check if the bot is admin in the group"""
    if update.effective_chat.type in ['group', 'supergroup']:
        bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logger.warning(f"Bot is not admin in chat {update.effective_chat.id}, member handler not functioning")
            return False
    return True

async def member_handler(update, context):
    """
    رسیدگی به افزودن اعضای جدید و اعطای امتیاز به کاربری که آنها را اضافه کرده است
    هر عضو جدید = 25 امتیاز
    """
    # بررسی ادمین بودن ربات
    if not await check_admin_status(update, context):
        return
    
    # بررسی کنید که آیا این یک رویداد عضو جدید است
    new_members = update.message.new_chat_members
    if not new_members:
        return
    
    # دریافت کاربری که اعضای جدید را اضافه کرده است
    if not update.message.from_user:
        return  # اطلاعات کاربر معتبر نیست
        
    adder_id = str(update.message.from_user.id)
    adder_name = update.message.from_user.first_name
    chat_id = str(update.effective_chat.id)
    
    # بررسی کنید که آیا کاربر خودش را اضافه کرده است (که نباید امتیاز بگیرد)
    if len(new_members) == 1 and new_members[0].id == int(adder_id):
        return
    
    # بارگذاری داده‌های امتیاز
    if os.path.exists('score.json'):
        try:
            with open('score.json', 'r', encoding='utf-8') as f:
                scores = json.load(f)
        except json.JSONDecodeError:
            logger.error("خطا در خواندن فایل score.json. یک فایل جدید ایجاد می‌شود.")
            scores = {}
    else:
        scores = {}
    
    # مقداردهی اولیه داده‌های چت اگر وجود ندارد
    if chat_id not in scores:
        scores[chat_id] = {}
    
    # مقداردهی اولیه داده‌های کاربر اگر وجود ندارد
    if adder_id not in scores[chat_id]:
        scores[chat_id][adder_id] = {
            "name": adder_name,
            "points": 0,
            "messages": 0
        }
    
    # شمارش تعداد اعضای جدید اضافه شده (به جز ربات‌ها)
    new_member_count = sum(1 for member in new_members if not member.is_bot)
    
    if new_member_count > 0:
        # اعطای 25 امتیاز به ازای هر عضو جدید
        points_awarded = 25 * new_member_count
        scores[chat_id][adder_id]["points"] += points_awarded
        scores[chat_id][adder_id]["name"] = adder_name  # به‌روزرسانی نام در صورت تغییر
        
        # اطلاع‌رسانی در گروه
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🇮🇷 تبریک {adder_name}!\n"
                 f"شما {new_member_count} عضو جدید به گروه اضافه کردید و {points_awarded} عجر معنوی دریافت کردید.\n"
                 f"عجر معنوی کل شما: {scores[chat_id][adder_id]['points']}"
        )
        
        logger.info(f"User {adder_id} added {new_member_count} new members to chat {chat_id} and received {points_awarded} points")
        
        # ذخیره امتیازات به‌روزرسانی شده
        try:
            with open('score.json', 'w', encoding='utf-8') as f:
                json.dump(scores, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"خطا در ذخیره فایل score.json: {e}")
        
        # حذف پیام بعد از 90 ثانیه
        async def delete_message_later(message):
            await asyncio.sleep(45)
            try:
                await message.delete()
                logger.info(f"Deleted notification message in chat {chat_id}")
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        
        # اجرای تابع حذف پیام به صورت غیرهمزمان
        asyncio.create_task(delete_message_later(sent_message))
