import os
from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def text_to_speech_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start text-to-speech feature"""
    keyboard = [
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    await update.message.reply_text(
        "🔊 **ميزة النطق الصوتي!**
"
        "أرسل لي أي نص صيني وسأقوم بنطقه لك.
"
        "استخدم /stop_tts لإنهاء هذه الميزة.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    context.user_data["tts_active"] = True

async def text_to_speech_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for TTS"""
    if not context.user_data.get("tts_active", False):
        return

    text = update.message.text
    if not text:
        return

    await update.message.chat.send_action("record_audio")

    try:
        tts = gTTS(text=text, lang='zh-CN')
        audio_path = f"temp_audio_{update.effective_user.id}.mp3"
        tts.save(audio_path)

        with open(audio_path, 'rb') as audio_file:
            await update.message.reply_audio(audio=audio_file)
        
        os.remove(audio_path)

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء تحويل النص إلى صوت: {str(e)}")

async def text_to_speech_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop text-to-speech feature"""
    if context.user_data.get("tts_active", False):
        context.user_data["tts_active"] = False
        await update.message.reply_text("✅ تم إنهاء ميزة النطق الصوتي. استخدم /tts للبدء من جديد.")
    else:
        await update.message.reply_text("لا توجد ميزة نطق صوتي نشطة حالياً.")

# Example usage in bot.py:
"""
from text_to_speech_feature import (
    text_to_speech_start, text_to_speech_message, text_to_speech_stop
)

# Add handlers
app.add_handler(CommandHandler("tts", text_to_speech_start))
app.add_handler(CommandHandler("stop_tts", text_to_speech_stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_message))
"""
