import os
import logging
import telebot # pip install pyTelegramBotAPI
from ocr_fill_pipeline import process_waste_image

# DRAFT: Telegram bot for Waste OCR
# รอใส่ Token จริงใน Environment Variable หรือ config file
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "รับภาพใบรายงานขยะแล้ว กำลังส่งไปประมวลผล OCR และกรอกฟอร์ม...")
    try:
        # 1. Download photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temp file
        image_path = f"/tmp/waste_report_{file_info.file_id}.jpg"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # 2. Process via OCR & Fill pipeline
        result = process_waste_image(image_path)
        
        # 3. Reply status
        bot.reply_to(message, f"✅ ดำเนินการสำเร็จ!\nกรอกข้อมูลไปแล้ว {len(result.get('rows', []))} รายการ\nยอดรวม: {result.get('total_kg', 0)} kg")
        
        # TODO: ส่ง Screenshot กลับให้ User เพื่อยืนยัน (ถ้ามี)
        # if 'screenshot' in result and os.path.exists(result['screenshot']):
        #     with open(result['screenshot'], 'rb') as photo:
        #         bot.send_photo(message.chat.id, photo)
                
    except Exception as e:
        logging.error("Error processing photo", exc_info=True)
        bot.reply_to(message, f"❌ เกิดข้อผิดพลาดในการทำงาน: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Waste OCR Telegram Bot...")
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logging.warning("Please set TELEGRAM_BOT_TOKEN environment variable.")
    else:
        bot.polling(none_stop=True)
