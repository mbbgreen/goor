import os
import logging
import tensorflow as tf
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import cv2
from io import BytesIO
import tempfile
from PIL import Image
import asyncio
import gzip  # برای باز کردن فایل‌های tgs

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token (get it from BotFather)
TOKEN = "7619620211:AAGY8KCvl5wiP0zhamEKYOmAUmnUzNYasB8"

# بهبود یافته NudeDetector برای تشخیص بهتر محتوای نامناسب در استیکرها
class NudeDetector:
    def __init__(self):
        # Load the MobileNet model (pre-trained on ImageNet)
        base_model = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3),
                                                      include_top=False,
                                                      weights='imagenet')
        
        # Add classification layers
        x = base_model.output
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dense(1024, activation='relu')(x)
        predictions = tf.keras.layers.Dense(2, activation='softmax')(x)  # 2 classes: safe, unsafe
        
        self.model = tf.keras.Model(inputs=base_model.input, outputs=predictions)
        
        # In a real implementation, you would load pre-trained weights for NSFW detection
        # self.model.load_weights('path_to_nsfw_weights.h5')
        
        logger.info("Nude detection model initialized")
    
    def preprocess_image(self, img_path):
        """Preprocess image for the model with improved error handling"""
        try:
            # برای فایل‌های تصویری از روش قبلی استفاده می‌کنیم
            if img_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
                img_array = tf.keras.preprocessing.image.img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0)
                return tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
            else:
                # برای سایر فرمت‌ها از OpenCV استفاده می‌کنیم
                img = cv2.imread(img_path)
                if img is None:
                    logger.error(f"Could not read image: {img_path}")
                    return None
                
                img = cv2.resize(img, (224, 224))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_array = np.expand_dims(img, axis=0)
                return tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def process_video(self, video_path, sample_rate=1):
        """Extract frames from video and check for NSFW content with improved sampling"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return 0
                
            # بررسی تعداد فریم‌های ویدیو
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # اگر تعداد فریم‌ها خیلی کم است (مثلا استیکر)، همه فریم‌ها را بررسی می‌کنیم
            if total_frames < 30:
                sample_rate = 1
            else:
                # برای ویدیوهای طولانی‌تر، حداکثر 30 فریم را بررسی می‌کنیم
                sample_rate = max(1, total_frames // 30)
            
            frame_count = 0
            max_nsfw_score = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every Nth frame
                if frame_count % sample_rate == 0:
                    # Save frame to temp file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        temp_path = temp_file.name
                        cv2.imwrite(temp_path, frame)
                    
                    # Check frame
                    score = self.detect_from_path(temp_path)
                    max_nsfw_score = max(max_nsfw_score, score)
                    
                    # Remove temp file
                    os.unlink(temp_path)
                
                frame_count += 1
            
            cap.release()
            
            # اگر نتوانستیم هیچ فریمی را پردازش کنیم
            if frame_count == 0:
                logger.warning(f"No frames processed in video: {video_path}")
                return 0
                
            return max_nsfw_score
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return 0
    
    def detect_from_path(self, img_path):
        
        """Detect if image contains NSFW content with improved skin detection"""
        
        try:
            # اول با مدل TensorFlow بررسی می‌کنیم (در یک پیاده‌سازی واقعی)
            preprocessed_img = self.preprocess_image(img_path)
            if preprocessed_img is None:
                return 0
            
            # بهبود روش تشخیص پوست
            img = cv2.imread(img_path)
            if img is None:
                logger.error(f"Could not read image for skin detection: {img_path}")
                return 0
                
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # تشخیص پوست با ترکیب چند فضای رنگی برای نتیجه بهتر
            
            # 1. تشخیص در فضای HSV
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            # محدوده پوست انسان در فضای HSV
            lower_skin_hsv1 = np.array([0, 48, 80], dtype=np.uint8)
            upper_skin_hsv1 = np.array([20, 255, 255], dtype=np.uint8)
            # محدوده دوم برای پوشش بیشتر تن‌های پوستی
            lower_skin_hsv2 = np.array([170, 30, 60], dtype=np.uint8) 
            upper_skin_hsv2 = np.array([180, 150, 255], dtype=np.uint8)
            
            mask_hsv1 = cv2.inRange(hsv, lower_skin_hsv1, upper_skin_hsv1)
            mask_hsv2 = cv2.inRange(hsv, lower_skin_hsv2, upper_skin_hsv2)
            mask_hsv = cv2.bitwise_or(mask_hsv1, mask_hsv2)
            
            # 2. تشخیص در فضای YCrCb
            ycrcb = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
            lower_skin_ycrcb = np.array([0, 138, 95], dtype=np.uint8)
            upper_skin_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
            mask_ycrcb = cv2.inRange(ycrcb, lower_skin_ycrcb, upper_skin_ycrcb)
            
            # ترکیب نتایج دو روش برای تشخیص دقیق‌تر
            mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)
            
            # بهبود ماسک با عملیات مورفولوژیکی برای حذف نویز
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # محاسبه نسبت پیکسل‌های پوست
            skin_ratio = np.sum(mask > 0) / (img.shape[0] * img.shape[1])
            
            # تشخیص پوست در نواحی پراهمیت تصویر (وسط تصویر)
            h, w = img.shape[:2]
            center_roi = mask[h//4:(h*3)//4, w//4:(w*3)//4]
            center_roi_ratio = np.sum(center_roi > 0) / center_roi.size if center_roi.size > 0 else 0
            
            # ترکیب نسبت‌ها با وزن بیشتر به مرکز تصویر
            weighted_ratio = (skin_ratio + center_roi_ratio * 2) / 3
            
            # تحلیل رنگ‌های غالب تصویر برای تشخیص بهتر
            colors = np.float32(img.reshape(-1, 3))
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            flags = cv2.KMEANS_RANDOM_CENTERS
            _, labels, centers = cv2.kmeans(colors, 5, None, criteria, 10, flags)
            
            # بررسی وجود رنگ‌های نزدیک به پوست در میان رنگ‌های غالب
            skin_tone_colors = 0
            for center in centers:
                # تبدیل به HSV برای بررسی محدوده پوست
                center_hsv = cv2.cvtColor(np.uint8([[center]]), cv2.COLOR_RGB2HSV)[0][0]
                if ((0 <= center_hsv[0] <= 20 or 170 <= center_hsv[0] <= 180) and 
                    30 <= center_hsv[1] <= 150 and 
                    60 <= center_hsv[2] <= 255):
                    skin_tone_colors += 1
            
            # ترکیب تمام معیارها برای نتیجه نهایی
            skin_color_ratio = skin_tone_colors / 5  # نسبت رنگ‌های پوست در رنگ‌های غالب
            
            # محاسبه امتیاز نهایی با ترکیب وزن‌دار معیارها
            nsfw_score = weighted_ratio * 0.6 + skin_color_ratio * 0.4
            nsfw_score = min(nsfw_score * 1.5, 1.0)  # تقویت امتیاز با محدودیت 1.0
            
            return nsfw_score
        except Exception as e:
            logger.error(f"Error in detection: {e}")
            return 0
    
    def is_nsfw(self, file_path, threshold=0.7, is_video=False):
        """Check if content is NSFW based on threshold"""
        try:
            if is_video:
                score = self.process_video(file_path)
            else:
                score = self.detect_from_path(file_path)
            
            # ثبت امتیاز برای دیباگ
            logger.info(f"NSFW score for {file_path}: {score}, threshold: {threshold}")
            
            return score > threshold, score
        except Exception as e:
            logger.error(f"Error checking NSFW: {e}")
            return False, 0

# Initialize detector
nude_detector = NudeDetector()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('سلام! من یک بات تشخیص محتوای نامناسب هستم. هر تصویر، ویدیو، گیف یا استیکری که ارسال شود را بررسی می‌کنم.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('این بات به صورت خودکار محتوای نامناسب را تشخیص می‌دهد و حذف می‌کند.')

async def process_sticker(file_path, is_video, is_animated):
    """تبدیل استیکر به فرمت قابل پردازش برای الگوریتم تشخیص"""
    try:
        # مسیر فایل خروجی
        output_path = file_path.rsplit('.', 1)[0]
        
        if is_video:
            # برای استیکرهای ویدیویی (webm)
            output_path += '_processed.mp4'
            
            # استفاده از ffmpeg برای تبدیل webm به mp4
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-i', file_path, '-vf', 'scale=224:224', output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            return output_path if os.path.exists(output_path) else None
            
        elif is_animated:
            # برای استیکرهای انیمیشن (tgs)
            output_path += '_processed.gif'
            
            # روش استاندارد با استفاده از gzip و ffmpeg
            try:
                # اول تبدیل tgs به json (tgs در واقع فایل Lottie فشرده شده با gzip است)
                temp_json = file_path.rsplit('.', 1)[0] + '.json'
                
                # باز کردن فایل tgs با استفاده از gzip
                with gzip.open(file_path, 'rb') as f_in:
                    json_data = f_in.read()
                
                # ذخیره محتوای json
                with open(temp_json, 'wb') as f_out:
                    f_out.write(json_data)
                
                # استفاده از ffmpeg برای تبدیل فریم‌های استخراج شده به تصویر
                # این روش فقط چند فریم از انیمیشن را استخراج می‌کند برای تحلیل
                for i in range(3):  # استخراج 3 فریم
                    frame_path = f"{output_path.rsplit('.', 1)[0]}_{i}.jpg"
                    process = await asyncio.create_subprocess_exec(
                        'ffmpeg', '-y', '-i', file_path, '-vf', f'select=eq(n\\,{i})', 
                        '-vframes', '1', frame_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    # اگر حداقل یک فریم استخراج شد، آن را برمی‌گردانیم
                    if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                        return frame_path
                
                # اگر نتوانستیم با ffmpeg فریم استخراج کنیم، از فایل json استفاده می‌کنیم
                # در اینجا می‌توان الگوریتم تحلیل فایل JSON را پیاده کرد
                # اما این کار پیچیده است و خارج از محدوده این مثال است
                
                # پاکسازی فایل موقت
                if os.path.exists(temp_json):
                    os.unlink(temp_json)
                
                logger.warning("Could not process animated sticker frames")
                return None
            except Exception as e:
                logger.error(f"Error processing animated sticker: {e}")
                return None
        else:
            # برای استیکرهای عادی (webp)
            output_path += '_processed.jpg'
            
            # تبدیل WebP به JPG برای پردازش بهتر
            img = Image.open(file_path)
            img.convert('RGB').save(output_path)
            
            return output_path if os.path.exists(output_path) else None
            
    except Exception as e:
        logger.error(f"Error processing sticker: {e}")
        return None

async def download_file(message, context):
    """Download a file from Telegram and save to a temporary file"""
    file_id = None
    is_video = False
    is_sticker = False
    caption = ""
    
    if message.photo:
        file_id = message.photo[-1].file_id  # Get the largest photo
    elif message.video:
        file_id = message.video.file_id
        is_video = True
    elif message.animation:  # GIF
        file_id = message.animation.file_id
        is_video = True
    elif message.sticker:
        file_id = message.sticker.file_id
        is_sticker = True
        # برای استیکرهای انیمیشن و ویدیویی تنظیم می‌کنیم
        is_video = message.sticker.is_video or message.sticker.is_animated
    elif message.document:
        file_id = message.document.file_id
        mime_type = message.document.mime_type
        if mime_type and ('image' in mime_type or 'video' in mime_type):
            is_video = 'video' in mime_type
        else:
            return None, False, caption, False  # Unsupported document type
    
    if message.caption:
        caption = message.caption
    
    if not file_id:
        return None, False, caption, False
    
    # Download the file
    file = await context.bot.get_file(file_id)
    
    # Create a temporary file with appropriate extension
    if is_sticker:
        if is_video:
            suffix = '.tgs' if message.sticker.is_animated else '.webm'
        else:
            suffix = '.webp'
    else:
        suffix = '.mp4' if is_video else '.jpg'
    
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temp_file.close()
    
    # Download file content
    await file.download_to_drive(temp_file.name)
    
    # پردازش استیکر به فرمت قابل پردازش برای تشخیص
    if is_sticker:
        processed_path = await process_sticker(temp_file.name, is_video, message.sticker.is_animated)
        if processed_path:
            # حذف فایل قدیمی اگر پردازش موفق بوده
            os.unlink(temp_file.name)
            return processed_path, is_video, caption, is_sticker
    
    return temp_file.name, is_video, caption, is_sticker

async def process_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process any media message for NSFW content"""
    chat_id = update.effective_chat.id
    message = update.message
    user = update.effective_user
    
    # Show the bot as typing while processing
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Download the file
    file_path, is_video, caption, is_sticker = await download_file(message, context)
    
    if not file_path:
        return
    
    try:
        # برای استیکرها، آستانه تشخیص را تنظیم می‌کنیم
        threshold = 0.8 if is_sticker else 0.7
        
        # Check if the content is NSFW
        is_nsfw, score = nude_detector.is_nsfw(file_path, threshold=threshold, is_video=is_video)
        
        # برای دیباگ، امتیاز تشخیص را ثبت می‌کنیم
        logger.info(f"NSFW detection score for {file_path}: {score}")
        
        if is_nsfw:
            # Delete the message
            await message.delete()
            
            # تعیین نوع محتوا برای پیام هشدار
            content_type = "استیکر" if is_sticker else "تصویر" if not is_video else "ویدیو/گیف"
            
            # Send warning message
            warning_text = f"⚠️ @{user.username or user.id} {content_type} شما به دلیل محتوای نامناسب حذف شد. لطفا از ارسال چنین محتوایی خودداری کنید."
            await context.bot.send_message(chat_id=chat_id, text=warning_text)
            
            # Log the incident
            logger.warning(f"NSFW content detected in {content_type} from user {user.id} in chat {chat_id} with score {score}")
    except Exception as e:
        logger.error(f"Error processing media: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)
        
        # پاکسازی فایل‌های موقت پردازش شده
        processed_path = file_path.rsplit('.', 1)[0] + '_processed.jpg'
        if os.path.exists(processed_path):
            os.unlink(processed_path)
        
        processed_path = file_path.rsplit('.', 1)[0] + '_processed.mp4'
        if os.path.exists(processed_path):
            os.unlink(processed_path)
        
        processed_path = file_path.rsplit('.', 1)[0] + '_processed.gif'
        if os.path.exists(processed_path):
            os.unlink(processed_path)
        
        # پاکسازی فریم‌های استخراج شده
        for i in range(3):
            frame_path = f"{file_path.rsplit('.', 1)[0]}_{i}.jpg"
            if os.path.exists(frame_path):
                os.unlink(frame_path)

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process text messages - can be expanded to check for inappropriate text"""
    # This is a placeholder for text moderation if needed
    pass

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add message handlers for different types of media
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | 
                                        filters.ANIMATION | filters.Document.IMAGE | 
                                        filters.Document.VIDEO | 
                                        filters.Sticker.ALL, process_media))
    
    # برای اطمینان از تشخیص همه استیکرها، فیلتر استیکر جداگانه اضافه می‌کنیم
    application.add_handler(MessageHandler(filters.Sticker.ALL, process_media))
    
    # Add text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
