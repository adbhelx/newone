
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Conversation states for the game
SELECTING_ANSWER = range(1)

# Dummy data for the game (replace with actual data from data.json if available)
# For now, we'll use a small hardcoded list for demonstration
GAME_WORDS = [
    {"chinese": "你好", "pinyin": "Nǐ hǎo", "arabic": "مرحباً"},
    {"chinese": "谢谢", "pinyin": "Xièxiè", "arabic": "شكراً"},
    {"chinese": "再见", "pinyin": "Zàijiàn", "arabic": "إلى اللقاء"},
    {"chinese": "爱", "pinyin": "Ài", "arabic": "حب"},
    {"chinese": "水", "pinyin": "Shuǐ", "arabic": "ماء"},
    {"chinese": "吃", "pinyin": "Chī", "arabic": "يأكل"},
    {"chinese": "喝", "pinyin": "Hē", "arabic": "يشرب"},
    {"chinese": "大", "pinyin": "Dà", "arabic": "كبير"},
    {"chinese": "小", "pinyin": "Xiǎo", "arabic": "صغير"},
    {"chinese": "是", "pinyin": "Shì", "arabic": "نعم / يكون"},
    {"chinese": "不", "pinyin": "Bù", "arabic": "لا / ليس"},
    {"chinese": "人", "pinyin": "Rén", "arabic": "شخص"},
    {"chinese": "学生", "pinyin": "Xuésheng", "arabic": "طالب"},
    {"chinese": "老师", "pinyin": "Lǎoshī", "arabic": "معلم"},
    {"chinese": "中国", "pinyin": "Zhōngguó", "arabic": "الصين"},
    {"chinese": "美国", "pinyin": "Měiguó", "arabic": "أمريكا"},
]

async def start_word_matching_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the word matching game"""
    if len(GAME_WORDS) < 4:
        await update.message.reply_text("لا توجد كلمات كافية لبدء اللعبة.")
        return ConversationHandler.END

    await generate_new_question(update, context)
    return SELECTING_ANSWER

async def generate_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates a new word matching question"""
    correct_word = random.choice(GAME_WORDS)
    incorrect_words = random.sample([w for w in GAME_WORDS if w != correct_word], 3)
    
    options = [correct_word] + incorrect_words
    random.shuffle(options)

    context.user_data["game_correct_answer"] = correct_word["chinese"]
    context.user_data["game_options"] = [w["chinese"] for w in options]

    keyboard = []
    for i, word in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}) {word['chinese']}", callback_data=f"game_answer_{word['chinese']}")])
    keyboard.append([InlineKeyboardButton("❌ إنهاء اللعبة", callback_data="game_end")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    question_text = (
        f"🎮 **لعبة تطابق الكلمات!**\n\n"
        f"ما معنى كلمة \"**{correct_word['arabic']}**\" بالصينية؟\n\n"
        f"**Pinyin:** {correct_word['pinyin']}\n"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the user's answer for the word matching game"""
    query = update.callback_query
    await query.answer()
    
    user_answer = query.data.split("game_answer_")[1]
    correct_answer = context.user_data.get("game_correct_answer")

    if user_answer == correct_answer:
        await query.edit_message_text("✅ إجابة صحيحة! أحسنت!\n\nلنلعب جولة أخرى.")
        await generate_new_question(update, context)
        return SELECTING_ANSWER
    else:
        await query.edit_message_text(
            f"❌ إجابة خاطئة. الإجابة الصحيحة كانت: **{correct_answer}**\n\nلنلعب جولة أخرى.",
            parse_mode='Markdown'
        )
        await generate_new_question(update, context)
        return SELECTING_ANSWER

async def end_word_matching_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ends the word matching game"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👋 تم إنهاء لعبة تطابق الكلمات. نأمل أن تكون قد استمتعت!")
    context.user_data.pop("game_correct_answer", None)
    context.user_data.pop("game_options", None)
    return ConversationHandler.END

# Example usage in main.py:
"""
from word_matching_game import (
    start_word_matching_game, check_answer, end_word_matching_game, SELECTING_ANSWER
)

# Add to ConversationHandler
word_matching_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_word_matching_game, pattern="^MENU_WORD_GAME$")],
    states={
        SELECTING_ANSWER: [
            CallbackQueryHandler(check_answer, pattern=r"^game_answer_"),
            CallbackQueryHandler(end_word_matching_game, pattern="^game_end$")
        ]
    },
    fallbacks=[CommandHandler("cancel", end_word_matching_game)]
)
app.add_handler(word_matching_conv_handler)
"""

