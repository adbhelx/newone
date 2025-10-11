"""
Enhanced Chinese Learning Bot v2.0
بوت تعلم اللغة الصينية المحسّن
مع الذكاء الاصطناعي ونظام الإنجازات
"""

import os
import json
import logging
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

# Import AI and Achievements
try:
    from ai_chat_feature import (
        ai_chat_start, ai_mode_select, ai_chat_message, 
        ai_chat_stop, ai_chat_stats
    )
    from achievements_system import AchievementSystem, format_achievement_notification
    AI_ENABLED = True
except Exception as e:
    print(f"AI features not available: {e}")
    AI_ENABLED = False

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
try:
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    ADMIN_USER_IDS = json.loads(os.environ.get('ADMIN_USER_IDS', '[]'))
    if not TOKEN:
        from config import TOKEN, ADMIN_USER_IDS
except Exception as e:
    logger.error(f"Configuration error: {e}")
    raise

# Data file
DB = "data.json"

# Conversation states
ADMIN_SECTION, ADMIN_TITLE, ADMIN_CONTENT, ADMIN_DELETE_CONFIRM, UPLOAD_FILE = range(5)

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_USER_IDS

def init_data():
    """Initialize data structure"""
    if os.path.exists(DB):
        try:
            with open(DB, encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in data file, creating new one")
    
    keys = [
        "HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6",
        "Quran", "Dictionary", "Stories", "GrammarLessons", "GrammarReview",
        "Dialogues", "Flashcards", "Quizzes", "PictureDictionary", 
        "GrammarTerms", "Proverbs", "Applications"
    ]
    data = {k: [] for k in keys}
    save_data(data)
    return data

def save_data(data):
    """Save data to file"""
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Build enhanced main menu with new features
def build_main_menu(user_id=None):
    """Build the main menu keyboard with new features"""
    items = [
        # Learning sections
        ("📚 HSK", "MENU_HSK"),
        ("🕌 القرآن", "SEC_Quran"),
        ("📕 القاموس", "SEC_Dictionary"),
        ("📖 القصص", "SEC_Stories"),
        ("📝 قواعد", "SEC_GrammarLessons"),
        ("💬 محادثات", "SEC_Dialogues"),
        
        # New AI Features
        ("🤖 محادثة AI", "AI_CHAT"),
        ("🏆 الإنجازات", "ACHIEVEMENTS"),
        ("📊 إحصائياتي", "MY_STATS"),
        
        # Other sections
        ("🃏 بطاقات", "SEC_Flashcards"),
        ("❓ اختبارات", "SEC_Quizzes"),
        ("📱 تطبيقات", "MENU_Apps"),
    ]
    
    kb = []
    row = []
    for i, (t, c) in enumerate(items, 1):
        row.append(InlineKeyboardButton(t, callback_data=c))
        if i % 3 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    
    # Add admin and help buttons
    admin_row = []
    if user_id and is_admin(user_id):
        admin_row.append(InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="MENU_Admin"))
    admin_row.append(InlineKeyboardButton("ℹ️ المساعدة", callback_data="HELP"))
    kb.append(admin_row)
    
    return kb

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user_id} ({user.username}) started the bot")
    
    # Track achievement
    if AI_ENABLED:
        try:
            achievement_system = AchievementSystem(user_id)
            newly_unlocked = achievement_system.update_stat("bot_starts", 1)
            
            # Send achievement notifications
            for achievement in newly_unlocked:
                await update.message.reply_text(
                    format_achievement_notification(achievement),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Achievement error: {e}")
    
    welcome_text = f"""
🇨🇳 **مرحباً بك في بوت تعلم اللغة الصينية!**

مرحباً {user.first_name}! 👋

🎯 **الميزات الجديدة**:
🤖 محادثة ذكية بالـ AI
🏆 نظام الإنجازات والنقاط
📊 تتبع التقدم الشخصي

📚 **الأقسام التعليمية**:
• جميع مستويات HSK (1-6)
• القرآن الكريم بالصينية
• قاموس ومحادثات وقصص
• اختبارات وبطاقات تعليمية

💡 **الأوامر المفيدة**:
/help - قائمة الأوامر الكاملة
/ai_chat - محادثة ذكية
/achievements - إنجازاتك
/mystats - إحصائياتك

اختر من القائمة أدناه للبدء! 👇
"""
    
    keyboard = build_main_menu(user_id)
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# /help handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📖 **دليل استخدام البوت**

🎯 **الأوامر الأساسية**:
/start - بدء البوت وعرض القائمة الرئيسية
/help - عرض هذه المساعدة
/cancel - إلغاء العملية الحالية

🤖 **المحادثة الذكية بالـ AI**:
/ai_chat - بدء محادثة ذكية
/stop_ai - إنهاء المحادثة
/ai_stats - إحصائيات المحادثة

🏆 **الإنجازات والإحصائيات**:
/achievements - عرض إنجازاتك
/mystats - عرض إحصائياتك الكاملة
/leaderboard - لوحة الصدارة (قريباً)

⚙️ **للمشرفين فقط**:
/admin - لوحة تحكم المشرفين

📚 **كيف تستخدم البوت؟**

1️⃣ **للتعلم العادي**:
   • اختر قسم من القائمة (HSK، القرآن، إلخ)
   • تصفح المحتوى المتاح
   • تعلم واستمتع!

2️⃣ **للمحادثة الذكية**:
   • اضغط 🤖 محادثة AI من القائمة
   • أو أرسل /ai_chat
   • اختر الوضع (معلم/محادثة/مترجم)
   • ابدأ الكتابة!

3️⃣ **لتتبع تقدمك**:
   • اضغط 🏆 الإنجازات من القائمة
   • أو اضغط 📊 إحصائياتي
   • شاهد تقدمك ونقاطك!

💡 **نصائح**:
• استخدم البوت يومياً لبناء سلسلة أيام
• جرب المحادثة الذكية للممارسة
• اجمع النقاط وافتح الإنجازات
• شارك البوت مع أصدقائك!

🌟 **الميزات القادمة**:
• ألعاب تعليمية تفاعلية
• نطق الكلمات بالصوت
• قصص تفاعلية متفرعة
• مكتبة الأغاني الصينية

📞 **الدعم**:
إذا واجهت أي مشكلة، تواصل مع المشرفين.

**استمتع بتعلم اللغة الصينية!** 🇨🇳📚✨
"""
    
    keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="BACK")]]
    await update.message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Handle button callbacks for new features
async def handle_new_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new feature button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "AI_CHAT":
        # Redirect to AI chat
        await ai_chat_start(update, context)
    
    elif query.data == "ACHIEVEMENTS":
        # Show achievements
        user_id = update.effective_user.id
        if AI_ENABLED:
            achievement_system = AchievementSystem(user_id)
            
            unlocked = achievement_system.get_unlocked_achievements()
            locked = achievement_system.get_locked_achievements()
            level_info = achievement_system.get_user_level()
            
            text = f"""
🏆 **إنجازاتك**

📊 المستوى: {level_info['icon']} {level_info['name_ar']} (المستوى {level_info['level']})
💎 النقاط: {level_info['points']}
🎯 التقدم: {level_info['progress']:.0f}%

✅ **مفتوحة** ({len(unlocked)}):
"""
            
            for ach in unlocked[:5]:
                text += f"\n{ach['icon']} {ach['name']} - {ach['points']} نقطة"
            
            if len(unlocked) > 5:
                text += f"\n... و {len(unlocked) - 5} إنجاز آخر"
            
            text += f"\n\n🔒 **مقفلة** ({len(locked)}):"
            
            for ach in locked[:3]:
                progress = ach.get('progress', 0)
                if isinstance(progress, bool):
                    progress_text = "0%"
                else:
                    progress_text = f"{progress:.0f}%"
                text += f"\n{ach['icon']} {ach['name']} - {progress_text}"
            
            text += "\n\n💡 استخدم /mystats للتفاصيل الكاملة"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="BACK")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ نظام الإنجازات غير متاح حالياً")
    
    elif query.data == "MY_STATS":
        # Show user stats
        user_id = update.effective_user.id
        if AI_ENABLED:
            achievement_system = AchievementSystem(user_id)
            summary = achievement_system.get_achievement_summary()
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="BACK")]]
            await query.edit_message_text(
                summary,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ الإحصائيات غير متاحة حالياً")
    
    elif query.data == "HELP":
        # Show help
        await help_command(update, context)

# Import all other handlers from original bot
# (For brevity, I'll indicate where they should be imported)
# ... [All original bot handlers] ...

def main():
    """Main function"""
    logger.info("Starting Enhanced Chinese Learning Bot v2.0...")
    
    if AI_ENABLED:
        logger.info("✅ AI Chat and Achievements enabled!")
    else:
        logger.warning("⚠️ AI features disabled - install requirements")
    
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # New feature handlers
    app.add_handler(CallbackQueryHandler(handle_new_features, pattern="^(AI_CHAT|ACHIEVEMENTS|MY_STATS|HELP)$"))
    
    if AI_ENABLED:
        # AI Chat handlers
        app.add_handler(CommandHandler("ai_chat", ai_chat_start))
        app.add_handler(CommandHandler("stop_ai", ai_chat_stop))
        app.add_handler(CommandHandler("ai_stats", ai_chat_stats))
        app.add_handler(CallbackQueryHandler(ai_mode_select, pattern=r"^ai_mode_"))
        
        # Achievement handlers
        app.add_handler(CommandHandler("achievements", lambda u, c: handle_new_features(u, c)))
        app.add_handler(CommandHandler("mystats", lambda u, c: handle_new_features(u, c)))
    
    # Note: Add all other handlers from original bot.py here
    # For now, this is a template showing the structure
    
    logger.info("Bot is running with enhanced features! 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

