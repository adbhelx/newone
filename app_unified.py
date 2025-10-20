
import os
import asyncio
import threading
from flask import Flask, request, jsonify, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import logging
import json
from datetime import datetime

# Import your bot's main functions and other features
# Ensure these files are in the same directory or properly imported
from main import (
    start, main_h, show_achievements, view_i, 
    adm_add_start, adm_add_sec, adm_add_title, adm_add_cont, 
    adm_view_start, adm_view_sec, adm_del_start, adm_del_sec,     adm_up_start, adm_up_sec, adm_receive_file, adm_up_finish, \
    adm_edit_start, adm_edit_sec, adm_edit_item, adm_edit_cont_start, 
    adm_edit_cont, adm_edit_title_start, adm_edit_title, 
    ai_chat_start, ai_mode_select, ai_chat_message, ai_chat_stop, ai_chat_stats, 
    text_to_speech_start, text_to_speech_message, text_to_speech_stop, 
    start_reminders_setup, set_daily_reminder, re_schedule_all_reminders, 
    start_word_matching_game, check_answer, end_word_matching_game, SELECTING_ANSWER, 
    show_leaderboard, 
    ADMIN_SECTION, ADMIN_TITLE, ADMIN_CONTENT, UPLOAD_FILE, 
    TOKEN, DB, data, save, is_admin, build_main_menu
)

# Configure logging for both Flask and Telegram Bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask App Setup
app = Flask(__name__)

# Telegram Bot Setup
application = ApplicationBuilder().token(TOKEN).build()

# Add handlers from your main.py
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(main_h, pattern="^(MENU_|BACK|SKIP_|SEC_)"))
application.add_handler(CallbackQueryHandler(show_achievements, pattern="^MENU_ACHIEVEMENTS$"))
application.add_handler(CallbackQueryHandler(view_i, pattern="^VIEW_"))

# AI Chat handlers
application.add_handler(CallbackQueryHandler(ai_chat_start, pattern="^MENU_AI_CHAT$"))
application.add_handler(CallbackQueryHandler(ai_mode_select, pattern="^AI_MODE_"))
application.add_handler(CallbackQueryHandler(ai_chat_stop, pattern="^AI_STOP$"))
application.add_handler(CallbackQueryHandler(ai_chat_stats, pattern="^AI_STATS$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_message))

# Text-to-Speech handlers
application.add_handler(CallbackQueryHandler(text_to_speech_start, pattern="^MENU_TTS$"))
application.add_handler(CallbackQueryHandler(text_to_speech_stop, pattern="^TTS_STOP$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_message))

# Daily Reminders handlers
application.add_handler(CallbackQueryHandler(start_reminders_setup, pattern="^MENU_REMINDERS$"))
application.add_handler(CommandHandler("setreminder", set_daily_reminder))
application.add_handler(CommandHandler("reschedule_reminders", re_schedule_all_reminders))

# Word Matching Game handlers
application.add_handler(CallbackQueryHandler(start_word_matching_game, pattern="^MENU_WORD_GAME$"))
application.add_handler(CallbackQueryHandler(end_word_matching_game, pattern="^WORD_GAME_STOP$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, check_answer))

# Leaderboard handler
application.add_handler(CallbackQueryHandler(show_leaderboard, pattern="^MENU_LEADERBOARD$"))

# Admin Conversation Handlers
conv_handler_add = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_add_start, pattern="^ADM_ADD$")],
    states={
        ADMIN_SECTION: [CallbackQueryHandler(adm_add_sec, pattern="^AAS_")],
        ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_title)],
        ADMIN_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_add_cont)],
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_add)

conv_handler_view = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_view_start, pattern="^ADM_VIEW$")],
    states={
        ADMIN_SECTION: [CallbackQueryHandler(adm_view_sec, pattern="^AVS_")],
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_view)

conv_handler_del = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_del_start, pattern="^ADM_DEL$")],
    states={
        ADMIN_SECTION: [CallbackQueryHandler(adm_del_sec, pattern="^ADS_")],
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_del)

conv_handler_up = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_up_start, pattern="^UP_")],
    states={
        UPLOAD_FILE: [
            MessageHandler(filters.Document.ALL, adm_receive_file),
            CallbackQueryHandler(adm_up_finish, pattern="^UP_FINISH_")
        ]
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_up)

conv_handler_edit = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_edit_start, pattern="^ADM_EDIT$")],
    states={
        ADMIN_SECTION: [CallbackQueryHandler(adm_edit_sec, pattern="^AES_")],
        ADMIN_TITLE: [CallbackQueryHandler(adm_edit_item, pattern="^AEI_")],
        ADMIN_CONTENT: [
            CallbackQueryHandler(adm_edit_cont_start, pattern="^AEC_CONT_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, adm_edit_cont),
            CallbackQueryHandler(adm_edit_title_start, pattern="^AEC_TITLE_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, adm_edit_title),
        ]
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_edit)

# Flask Routes for Web App
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sections')
def get_sections():
    data_loaded = data # Assuming 'data' is loaded from main.py
    sections = []
    
    section_info = {
        "HSK1": {"name": "HSK المستوى 1", "icon": "📚", "category": "HSK"},
        "HSK2": {"name": "HSK المستوى 2", "icon": "📚", "category": "HSK"},
        "HSK3": {"name": "HSK المستوى 3", "icon": "📚", "category": "HSK"},
        "HSK4": {"name": "HSK المستوى 4", "icon": "📚", "category": "HSK"},
        "HSK5": {"name": "HSK المستوى 5", "icon": "📚", "category": "HSK"},
        "HSK6": {"name": "HSK المستوى 6", "icon": "📚", "category": "HSK"},
        "Quran": {"name": "القرآن الكريم", "icon": "🕌", "category": "محتوى"},
        "Dictionary": {"name": "القاموس", "icon": "🗂️", "category": "محتوى"},
        "Stories": {"name": "القصص", "icon": "📖", "category": "محتوى"},
        "GrammarLessons": {"name": "دروس القواعد", "icon": "🔤", "category": "تعليم"},
        "GrammarReview": {"name": "مراجعة القواعد", "icon": "📑", "category": "تعليم"},
        "Dialogues": {"name": "المحادثات", "icon": "💬", "category": "تعليم"},
        "Flashcards": {"name": "البطاقات التعليمية", "icon": "🃏", "category": "تدريب"},
        "Quizzes": {"name": "الاختبارات", "icon": "❓", "category": "تدريب"},
        "PictureDictionary": {"name": "معجم صور", "icon": "📷", "category": "محتوى"},
        "GrammarTerms": {"name": "مصطلحات القواعد", "icon": "📝", "category": "محتوى"},
        "Proverbs": {"name": "الأمثال", "icon": "💭", "category": "محتوى"},
        "Applications": {"name": "التطبيقات", "icon": "📱", "category": "أدوات"}
    }
    
    for section_id, items in data_loaded.items():
        info = section_info.get(section_id, {
            "name": section_id,
            "icon": "📂",
            "category": "أخرى"
        })
        sections.append({
            "id": section_id,
            "name": info["name"],
            "icon": info["icon"],
            "category": info["category"],
            "count": len(items)
        })
    
    return jsonify(sections)

@app.route('/api/section/<section_id>')
def get_section(section_id):
    data_loaded = data
    items = data_loaded.get(section_id, [])
    
    return jsonify({
        "section": section_id,
        "items": items,
        "count": len(items)
    })

@app.route('/api/item/<section_id>/<int:item_id>')
def get_item(section_id, item_id):
    data_loaded = data
    items = data_loaded.get(section_id, [])
    item = next((x for x in items if x["id"] == item_id), None)
    
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/stats')
def get_stats():
    data_loaded = data
    
    total_items = sum(len(items) for items in data_loaded.values())
    sections_with_content = sum(1 for items in data_loaded.values() if items)
    
    stats = {
        "total_sections": len(data_loaded),
        "sections_with_content": sections_with_content,
        "total_items": total_items,
        "last_updated": datetime.now().isoformat()
    }
    
    return jsonify(stats)

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    data_loaded = data
    results = []
    
    for section_id, items in data_loaded.items():
        for item in items:
            if query in item["title"].lower() or query in str(item.get("content", "")).lower():
                results.append({
                    "section": section_id,
                    "item": item
                })
    
    return jsonify(results)

@app.route('/health')
def health():
    # This endpoint will be pinged by Render to keep the service alive
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_status": "running" if telegram_bot_thread.is_alive() else "stopped"
    })

# Function to run the Telegram bot
def run_bot():
    logger.info("Starting Telegram bot polling...")
    application.run_polling(drop_pending_updates=True)
    logger.info("Telegram bot polling stopped.")

# Start the Telegram bot in a separate thread
telegram_bot_thread = threading.Thread(target=run_bot)
telegram_bot_thread.daemon = True # Allow main program to exit even if thread is running

if __name__ == '__main__':
    # Start the bot thread if not already started
    if not telegram_bot_thread.is_alive():
        telegram_bot_thread.start()
        logger.info("Telegram bot thread started.")

    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Flask app starting on port {port}")
    app.run(host='0.0.0.0', port=port)


