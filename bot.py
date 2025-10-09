import logging, json, os
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

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment or config file
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
    try:
        with open(DB, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

data = init_data()

# Conversation states
ADMIN_SECTION, ADMIN_TITLE, ADMIN_CONTENT, UPLOAD_FILE = range(4)

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_USER_IDS

# Build main keyboard
def build_main_menu():
    """Build the main menu keyboard"""
    items = [
        ("📚 HSK", "MENU_HSK"),
        ("🕌 القرآن", "SEC_Quran"),
        ("🗂️ القاموس", "SEC_Dictionary"),
        ("📖 القصص", "SEC_Stories"),
        ("🔤 قواعد", "SEC_GrammarLessons"),
        ("📑 مراجعة", "SEC_GrammarReview"),
        ("💬 محادثات", "SEC_Dialogues"),
        ("🃏 Flashcards", "SEC_Flashcards"),
        ("❓ كويزات", "SEC_Quizzes"),
        ("📷 معجم صور", "SEC_PictureDictionary"),
        ("📱 التطبيقات", "MENU_Apps"),
        ("⚙️ Admin", "MENU_Admin")
    ]
    kb, row = [], []
    for i, (t, c) in enumerate(items, 1):
        row.append(InlineKeyboardButton(t, callback_data=c))
        if i % 3 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return kb

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    await update.message.reply_text(
        f"مرحبًا {user.first_name}! 👋\n\n"
        "أهلاً بك في بوت تعلم اللغة الصينية 🇨🇳\n"
        "اختر قسمًا من القائمة أدناه:",
        reply_markup=InlineKeyboardMarkup(build_main_menu())
    )

# /help handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **دليل استخدام البوت**

**الأقسام المتاحة:**
• HSK - دروس مستويات HSK من 1 إلى 6
• القرآن - القرآن الكريم باللغة الصينية
• القاموس - قاموس عربي-صيني
• القصص - قصص تعليمية
• القواعد - دروس القواعد
• المحادثات - محادثات يومية
• Flashcards - بطاقات تعليمية
• الكويزات - اختبارات تفاعلية

**للمشرفين:**
يمكنك إضافة وحذف واستعراض المحتوى من لوحة المشرف.

استخدم /start للعودة إلى القائمة الرئيسية.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Main callback handler
async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu callbacks"""
    q = update.callback_query
    await q.answer()
    d = q.data

    # Skip placeholders
    if d.startswith("SKIP_"):
        sec = d.split("_", 1)[1]
        return await q.edit_message_text(f"قسم {sec} قريبًا! 🔥")

    # Applications submenu
    if d == "MENU_Apps":
        apps = [
            ("📖 قصص تفاعلية", "SKIP_Stories"),
            ("📝 قواعد تفاعلية", "SKIP_Rules"),
            ("🔄 مراجعة تفاعلية", "SKIP_Review"),
            ("💬 محادثات تفاعلية", "SKIP_Convo"),
            ("🃏 فلاش كاردز تفاعلية", "SKIP_Flashcards"),
            ("❓ كويزات تفاعلية", "SKIP_Quizzes")
        ]
        kb, row = [], []
        for i, (t, c) in enumerate(apps, 1):
            row.append(InlineKeyboardButton(t, callback_data=c))
            if i % 2 == 0:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        return await q.edit_message_text(
            "قسم التطبيقات التفاعلية:\n\nاختر تطبيقًا:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # HSK levels menu
    if d == "MENU_HSK":
        kb, row = [], []
        for i in range(1, 7):
            count = len(data.get(f"HSK{i}", []))
            row.append(InlineKeyboardButton(
                f"HSK{i} ({count})", 
                callback_data=f"SEC_HSK{i}"
            ))
            if len(row) == 3:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        return await q.edit_message_text(
            "اختر مستوى HSK:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # Back to main
    if d == "BACK":
        await q.edit_message_text(
            "القائمة الرئيسية:\nاختر قسمًا:",
            reply_markup=InlineKeyboardMarkup(build_main_menu())
        )
        return ConversationHandler.END

    # Admin panel
    if d == "MENU_Admin":
        if not is_admin(q.from_user.id):
            return await q.edit_message_text("⛔ هذا القسم للمشرفين فقط.")
        
        total_items = sum(len(items) for items in data.values())
        kb = [
            [InlineKeyboardButton("➕ إضافة محتوى", callback_data="ADM_ADD")],
            [InlineKeyboardButton("📝 استعراض المحتوى", callback_data="ADM_VIEW")],
            [InlineKeyboardButton("❌ حذف محتوى", callback_data="ADM_DEL")],
            [InlineKeyboardButton("📁 رفع ملف", callback_data="ADM_UP")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="ADM_STATS")],
            [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
        ]
        return await q.edit_message_text(
            f"لوحة المشرف 🛠️\n\nإجمالي المحتوى: {total_items} عنصر",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # Statistics for admin
    if d == "ADM_STATS":
        if not is_admin(q.from_user.id):
            return await q.edit_message_text("⛔ للمشرفين فقط.")
        
        stats = "📊 **إحصائيات المحتوى:**\n\n"
        for sec, items in data.items():
            if items:
                stats += f"• {sec}: {len(items)} عنصر\n"
        
        kb = [[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")]]
        return await q.edit_message_text(
            stats,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )

    # Section display
    if d.startswith("SEC_"):
        sec = d.split("_", 1)[1]
        items = data.get(sec, [])
        
        if not items:
            kb = []
            if is_admin(q.from_user.id):
                kb.append([InlineKeyboardButton("➕ إضافة محتوى", callback_data=f"UPSEC_{sec}")])
            kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
            return await q.edit_message_text(
                f"قسم {sec} فارغ حالياً.\n\nلا يوجد محتوى متاح.",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        
        kb, row = [], []
        for it in items:
            row.append(InlineKeyboardButton(
                it["title"][:30] + "..." if len(it["title"]) > 30 else it["title"],
                callback_data=f"VIEW_{sec}_{it['id']}"
            ))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        
        if is_admin(q.from_user.id):
            kb.append([InlineKeyboardButton("➕ إضافة محتوى", callback_data=f"UPSEC_{sec}")])
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        
        return await q.edit_message_text(
            f"قسم {sec} ({len(items)} عنصر):",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# View item handler
async def view_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View a specific item"""
    q = update.callback_query
    await q.answer()
    
    try:
        _, sec, sid = q.data.split("_", 2)
        idx = int(sid)
        itm = next((x for x in data.get(sec, []) if x["id"] == idx), None)
        
        if not itm:
            return await q.edit_message_text("⚠️ العنصر غير موجود.")
        
        content = itm["content"]
        
        # Check if content is a file_id (starts with specific patterns)
        if content.startswith(("BQA", "AgA", "CQA")):
            # It's a file_id, send as document
            await q.message.reply_document(
                document=content,
                caption=f"📄 {itm['title']}"
            )
        else:
            # It's text content
            await q.message.reply_text(
                f"📄 **{itm['title']}**\n\n{content}",
                parse_mode='Markdown'
            )
        
        # Return to section view
        kb = [[InlineKeyboardButton("◀️ رجوع للقسم", callback_data=f"SEC_{sec}")]]
        await q.edit_message_text(
            f"تم إرسال: {itm['title']}",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        
    except Exception as e:
        logger.error(f"Error viewing item: {e}")
        await q.edit_message_text("⚠️ حدث خطأ أثناء عرض المحتوى.")

# Admin: Add item
async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add item conversation"""
    q = update.callback_query
    await q.answer()
    
    kb = [[InlineKeyboardButton(sec, callback_data=f"AAS_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="MENU_Admin")])
    
    await q.edit_message_text(
        "اختر القسم للإضافة إليه:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ADMIN_SECTION

async def admin_add_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select section for adding"""
    q = update.callback_query
    await q.answer()
    
    context.user_data["sec"] = q.data.split("_", 1)[1]
    await q.edit_message_text(
        f"✏️ القسم: {context.user_data['sec']}\n\n"
        "أرسل عنوان العنصر:"
    )
    return ADMIN_TITLE

async def admin_add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive title for new item"""
    context.user_data["title"] = update.message.text
    await update.message.reply_text(
        f"✅ العنوان: {update.message.text}\n\n"
        "🌐 الآن أرسل المحتوى:\n"
        "• نص عادي\n"
        "• رابط\n"
        "• ملف (PDF, صورة, فيديو، صوت)"
    )
    return ADMIN_CONTENT

async def admin_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive content for new item"""
    sec = context.user_data["sec"]
    title = context.user_data["title"]
    msg = update.message
    
    # Check if it's a file
    if msg.document:
        content = msg.document.file_id
    elif msg.photo:
        content = msg.photo[-1].file_id
    elif msg.video:
        content = msg.video.file_id
    elif msg.audio:
        content = msg.audio.file_id
    elif msg.text:
        content = msg.text.strip()
    else:
        await msg.reply_text("⚠️ نوع المحتوى غير مدعوم. أرسل نصاً أو ملفاً.")
        return ADMIN_CONTENT
    
    # Add to data
    nid = max([item["id"] for item in data[sec]] or [0]) + 1
    data[sec].append({"id": nid, "title": title, "content": content})
    save_data(data)
    
    await msg.reply_text(
        f"✅ تمت الإضافة بنجاح!\n\n"
        f"القسم: {sec}\n"
        f"العنوان: {title}\n"
        f"ID: {nid}"
    )
    return ConversationHandler.END

# Admin: View items
async def admin_view_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start view items conversation"""
    q = update.callback_query
    await q.answer()
    
    kb = [[InlineKeyboardButton(f"{sec} ({len(data[sec])})", callback_data=f"AVS_{sec}")] 
          for sec in data.keys()]
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="MENU_Admin")])
    
    await q.edit_message_text(
        "اختر القسم للاستعراض:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ADMIN_SECTION

async def admin_view_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View items in section"""
    q = update.callback_query
    await q.answer()
    
    sec = q.data.split("_", 1)[1]
    items = data[sec]
    
    if not items:
        text = f"قسم {sec} فارغ."
    else:
        text = f"📋 **محتويات قسم {sec}:**\n\n"
        for i in items:
            content_type = "ملف" if i["content"].startswith(("BQA", "AgA", "CQA")) else "نص"
            text += f"• ID: {i['id']} - {i['title']} ({content_type})\n"
    
    kb = [[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ConversationHandler.END

# Admin: Delete item
async def admin_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start delete item conversation"""
    q = update.callback_query
    await q.answer()
    
    kb = [[InlineKeyboardButton(f"{sec} ({len(data[sec])})", callback_data=f"ADS_{sec}")] 
          for sec in data.keys() if data[sec]]
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="MENU_Admin")])
    
    await q.edit_message_text(
        "اختر القسم للحذف منه:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ADMIN_SECTION

async def admin_delete_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select section for deletion"""
    q = update.callback_query
    await q.answer()
    
    sec = q.data.split("_", 1)[1]
    context.user_data["sec"] = sec
    
    items_list = "\n".join(f"• ID: {i['id']} - {i['title']}" for i in data[sec])
    await q.edit_message_text(
        f"📋 عناصر قسم {sec}:\n\n{items_list}\n\n"
        "✏️ أرسل ID العنصر لحذفه:"
    )
    return ADMIN_TITLE

async def admin_delete_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete item by ID"""
    sec = context.user_data["sec"]
    
    try:
        idx = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ ID خاطئ. أرسل رقماً صحيحاً.")
        return ADMIN_TITLE
    
    before = len(data[sec])
    item_to_delete = next((x for x in data[sec] if x["id"] == idx), None)
    
    if item_to_delete:
        data[sec] = [x for x in data[sec] if x["id"] != idx]
        save_data(data)
        await update.message.reply_text(
            f"✅ تم الحذف بنجاح!\n\n"
            f"العنصر: {item_to_delete['title']}\n"
            f"من القسم: {sec}"
        )
    else:
        await update.message.reply_text("⚠️ لم أجد العنصر بهذا ID.")
    
    return ConversationHandler.END

# Admin: Upload file
async def admin_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start upload file conversation"""
    q = update.callback_query
    await q.answer()
    
    kb = [[InlineKeyboardButton(sec, callback_data=f"UPSEC_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="MENU_Admin")])
    
    await q.edit_message_text(
        "اختر القسم لرفع ملف إليه:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ADMIN_SECTION

async def admin_upload_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select section for upload"""
    q = update.callback_query
    await q.answer()
    
    context.user_data["sec"] = q.data.split("_", 1)[1]
    await q.edit_message_text(
        f"📁 القسم: {context.user_data['sec']}\n\n"
        "أرسل الملف الآن:\n"
        "• PDF\n"
        "• صورة\n"
        "• فيديو\n"
        "• صوت"
    )
    return UPLOAD_FILE

async def admin_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save uploaded file"""
    msg = update.message
    sec = context.user_data["sec"]
    
    # Determine file type and get file_id
    if msg.document:
        fid = msg.document.file_id
        name = msg.document.file_name or f"document_{msg.document.file_unique_id}"
    elif msg.video:
        fid = msg.video.file_id
        name = msg.video.file_name or f"video_{msg.video.file_unique_id}.mp4"
    elif msg.audio:
        fid = msg.audio.file_id
        name = msg.audio.file_name or f"audio_{msg.audio.file_unique_id}.mp3"
    elif msg.photo:
        fid = msg.photo[-1].file_id
        name = f"photo_{msg.photo[-1].file_unique_id}.jpg"
    else:
        return await msg.reply_text(
            "⛔ نوع الملف غير مدعوم.\n"
            "أرسل: PDF، صورة، فيديو، أو صوت."
        )
    
    # Add to data
    nid = max([item["id"] for item in data[sec]] or [0]) + 1
    data[sec].append({"id": nid, "title": name, "content": fid})
    save_data(data)
    
    await msg.reply_text(
        f"✅ تم رفع الملف بنجاح!\n\n"
        f"القسم: {sec}\n"
        f"الاسم: {name}\n"
        f"ID: {nid}\n"
        f"File ID: `{fid}`",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ حدث خطأ أثناء معالجة طلبك.\n"
                "يرجى المحاولة مرة أخرى أو التواصل مع المشرف."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

def main():
    """Start the bot"""
    logger.info("Starting bot...")
    
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Main menu handler
    app.add_handler(CallbackQueryHandler(
        main_handler, 
        pattern=r"^(MENU_|SEC_|BACK|SKIP_|ADM_STATS)"
    ))
    
    # View item handler
    app.add_handler(CallbackQueryHandler(view_item, pattern=r"^VIEW_"))
    
    # Admin: Add item conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_start, pattern="^ADM_ADD$")],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_add_section, pattern=r"^AAS_")],
            ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_title)],
            ADMIN_CONTENT: [
                MessageHandler(
                    (filters.TEXT | filters.Document.ALL | filters.PHOTO | 
                     filters.VIDEO | filters.AUDIO) & ~filters.COMMAND,
                    admin_add_content
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Admin: View items conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_view_start, pattern="^ADM_VIEW$")],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_view_section, pattern=r"^AVS_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Admin: Delete item conversation
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_delete_start, pattern="^ADM_DEL$")],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_delete_section, pattern=r"^ADS_")],
            ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_delete_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Admin: Upload file conversation
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_upload_start, pattern="^ADM_UP$"),
            CallbackQueryHandler(admin_upload_section, pattern=r"^UPSEC_")
        ],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_upload_section, pattern=r"^UPSEC_")],
            UPLOAD_FILE: [
                MessageHandler(
                    filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
                    admin_receive_file
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Start polling
    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
