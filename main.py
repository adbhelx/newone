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
from config import TOKEN, ADMIN_USER_IDS
from ai_chat_feature import (
    ai_chat_start, ai_mode_select, ai_chat_message, 
    ai_chat_stop, ai_chat_stats
)
from achievements_system import AchievementSystem, format_achievement_notification
from text_to_speech_feature import (
    text_to_speech_start, text_to_speech_message, text_to_speech_stop
)



# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data file
DB = "data.json"
if os.path.exists(DB):
    with open(DB, encoding='utf-8') as f:
        data = json.load(f)
else:
    keys = [
        "HSK1","HSK2","HSK3","HSK4","HSK5","HSK6",
        "Quran","Dictionary","Stories","GrammarLessons","GrammarReview",
        "Dialogues","Flashcards","Quizzes","PictureDictionary","GrammarTerms","Proverbs",
        # new Applications section
        "Applications"
    ]
    data = {k: [] for k in keys}
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Conversation states
ADMIN_SECTION, ADMIN_TITLE, ADMIN_CONTENT, UPLOAD_FILE = range(4)

def save():
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

# Build main keyboard
def build_main_menu():
    items = [
        ("📚 HSK", "MENU_HSK"),
        ("🕌 القرآن", "MENU_Quran"),
        ("🗂️ القاموس", "MENU_Dictionary"),
        ("📖 القصص", "MENU_Stories"),
        ("🔤 قواعد", "MENU_GrammarLessons"),
        ("📑 مراجعة", "MENU_GrammarReview"),
        ("💬 محادثات", "MENU_Dialogues"),
        ("🃏 Flashcards", "MENU_Flashcards"),
        ("❓ كويزات", "MENU_Quizzes"),
        ("📷 معجم صور", "MENU_PictureDictionary"),
        ("📱 التطبيقات", "MENU_Apps"),
        ("🤖 AI Chat", "MENU_AI_CHAT"),
        ("🏆 الإنجازات", "MENU_ACHIEVEMENTS"),
        ("🔊 نطق صوتي", "MENU_TTS"),
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
    await update.message.reply_text("مرحبًا! اختر قسمًا:", reply_markup=InlineKeyboardMarkup(build_main_menu()))

# Main callback handler
async def main_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data

    # Skip placeholders
    if d.startswith("SKIP_"):
        sec = d.split("_", 1)[1]
        return await q.edit_message_text(f"{sec}: قريبًا🔥")

    # Applications submenu
    if d == "MENU_Apps":
        apps = [
            ("🚧 قصص سكب", "SKIP_Stories"),
            ("🚧 قواعد سكب", "SKIP_Rules"),
            ("🚧 مراجعة سكب", "SKIP_Review"),
            ("🚧 محادثات سكب", "SKIP_Convo"),
            ("🚧 فلاش كاردز سكب", "SKIP_Flashcards"),
            ("🚧 كويزات سكب", "SKIP_Quizzes")
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
        return await q.edit_message_text("قسم التطبيقات:", reply_markup=InlineKeyboardMarkup(kb))

    # HSK levels menu
    if d == "MENU_HSK":
        kb, row = [], []
        for i in range(1, 7):
            row.append(InlineKeyboardButton(f"HSK{i}", callback_data=f"SEC_HSK{i}"))
            if len(row) == 3:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        return await q.edit_message_text("اختر مستوى HSK:", reply_markup=InlineKeyboardMarkup(kb))

    # Back to main
    if d == "BACK":
        return await start(update, context)

    # AI Chat
    if d == "MENU_AI_CHAT":
        return await ai_chat_start(update, context)

    # Achievements
    if d == "MENU_ACHIEVEMENTS":
        return await show_achievements(update, context)

    # Text-to-Speech
    if d == "MENU_TTS":
        return await text_to_speech_start(update, context)

    # Admin panel
    if d == "MENU_Admin":
        if not is_admin(q.from_user.id):
            return await q.edit_message_text("⛔ للمشرفين فقط.")
        kb = [
            [InlineKeyboardButton("➕ إضافة", callback_data="ADM_ADD")],
            [InlineKeyboardButton("📝 استعراض", callback_data="ADM_VIEW")],
            [InlineKeyboardButton("❌ حذف", callback_data="ADM_DEL")],
            [InlineKeyboardButton("📁 رفع ملف", callback_data="ADM_UP")],
            [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
        ]
        return await q.edit_message_text("لوحة المشرف:", reply_markup=InlineKeyboardMarkup(kb))

    # Section display or upload entry
    if d.startswith("SEC_") or d.startswith("MENU_"):
        sec = d.split("_",1)[1]
        items = data.get(sec, [])
        kb, row = [], []
        for it in items:
            row.append(InlineKeyboardButton(it["title"], callback_data=f"VIEW_{sec}_{it['id']}"))
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        if is_admin(q.from_user.id):
            kb.append([InlineKeyboardButton("📁 رفع هنا", callback_data=f"UP_{sec}")])
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        return await q.edit_message_text(f"قسم {sec}:", reply_markup=InlineKeyboardMarkup(kb))

# view item -> send document by file_id
async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    achievement_system = AchievementSystem(user_id)

    summary = achievement_system.get_achievement_summary()
    unlocked_achievements = achievement_system.get_unlocked_achievements()
    locked_achievements = achievement_system.get_locked_achievements()

    text = summary
    if unlocked_achievements:
        text += "\n\n🌟 **إنجازاتك المفتوحة:**\n"
        for ach in unlocked_achievements:
            text += f"{ach['icon']} {ach['name']}\n"
    
    if locked_achievements:
        text += "\n\n🔒 **إنجازات لم تفتح بعد:**\n"
        for ach in locked_achievements:
            progress_bar = "█" * int(ach['progress'] / 10) + "░" * (10 - int(ach['progress'] / 10))
            text += f"{ach['icon']} {ach['name']} ({ach['current']}/{ach['target']})\n`{progress_bar}` {ach['progress']:.0f}%\n"

    await q.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]]))

async def view_i(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, sec, sid = q.data.split("_")
    idx = int(sid)
    itm = next((x for x in data.get(sec, []) if x["id"] == idx), None)
    if not itm:
        return await q.edit_message_text("⚠️ غير موجود.")
    await q.message.reply_document(document=itm["content"], filename=itm["title"])
    return await main_h(update, context)

# 1) Add item
async def adm_add_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton(sec, callback_data=f"AAS_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")])
    await q.edit_message_text("اختر القسم للإضافة إليه:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_SECTION

async def adm_add_sec(update: Update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["sec"] = q.data.split("_", 1)[1]
    await q.edit_message_text("✏️ أرسل عنوان العنصر:")
    return ADMIN_TITLE

async def adm_add_title(update: Update, context):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("🌐 أرسل محتوى (نص أو رابط أو file_id):")
    return ADMIN_CONTENT

async def adm_add_cont(update: Update, context):
    sec = context.user_data["sec"]
    title = context.user_data["title"]
    content = update.message.text.strip()
    nid = max([x["id"] for x in data[sec]] or [0]) + 1
    data[sec].append({"id": nid, "title": title, "content": content})
    save()
    await update.message.reply_text(f"✅ أضيف إلى {sec}: {title}")
    return ConversationHandler.END

# 2) View list
async def adm_view_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton(sec, callback_data=f"AVS_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")])
    await q.edit_message_text("اختر القسم للاستعراض:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_SECTION

async def adm_view_sec(update: Update, context):
    q = update.callback_query
    await q.answer()
    sec = q.data.split("_", 1)[1]
    lst = "\n".join(f"- {i['title']} (id={i['id']})" for i in data[sec])
    await q.edit_message_text(f"عناصر {sec}:\n{lst}")
    return ConversationHandler.END

# 3) Delete item
async def adm_del_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton(sec, callback_data=f"ADS_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")])
    await q.edit_message_text("اختر القسم للحذف منه:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_SECTION

async def adm_del_sec(update: Update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["sec"] = q.data.split("_", 1)[1]
    await q.edit_message_text("✏️ أرسل id العنصر لحذفه:")
    return ADMIN_TITLE

async def adm_del_id(update: Update, context):
    sec = context.user_data["sec"]
    try:
        idx = int(update.message.text)
    except:
        await update.message.reply_text("⚠️ id خاطئ.")
        return ADMIN_TITLE
    before = len(data[sec])
    data[sec] = [x for x in data[sec] if x["id"] != idx]
    save()
    if len(data[sec]) < before:
        await update.message.reply_text("✅ تم الحذف.")
    else:
        await update.message.reply_text("⚠️ لم أجد العنصر.")
    return ConversationHandler.END

# 4) Upload file -> store file_id
async def adm_up_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton(sec, callback_data=f"UPSEC_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")])
    await q.edit_message_text("اختر القسم لرفع ملف إليه:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_SECTION

async def adm_up_sec(update: Update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["sec"] = q.data.split("_", 1)[1]
    await q.edit_message_text(f"✏️ أرسل الملف للقسم {context.user_data['sec']}:")
    return UPLOAD_FILE

async def adm_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    sec = context.user_data["sec"]
    if msg.document:
        fid, name = msg.document.file_id, msg.document.file_name
    elif msg.video:
        fid, name = msg.video.file_id, "video.mp4"
    elif msg.audio:
        fid, name = msg.audio.file_id, "audio"+msg.audio.file_unique_id
    elif msg.photo:
        fid, name = msg.photo[-1].file_id, "photo"+msg.photo[-1].file_unique_id
    else:
        return await msg.reply_text("⛔ أرسل ملف PDF/صوت/فيديو/صورة.")

    nid = max([x["id"] for x in data[sec]] or [0]) + 1
    data[sec].append({"id": nid, "title": name, "content": fid})
    save()
    await msg.reply_text(f"✅ تم حفظ الملف في {sec}:\n`{name}`\nfile_id=`{fid}`", parse_mode='Markdown')
    return ConversationHandler.END

# register handlers
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(main_h, pattern=r"^(MENU_|SEC_|BACK|SKIP_)"))
app.add_handler(CallbackQueryHandler(view_i, pattern=r"^VIEW_"))

app.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_add_start, pattern="^ADM_ADD$")],
    states={
      ADMIN_SECTION:[CallbackQueryHandler(adm_add_sec,pattern=r"^AAS_")],
      ADMIN_TITLE:[MessageHandler(filters.TEXT & ~filters.COMMAND,adm_add_title)],
      ADMIN_CONTENT:[MessageHandler(filters.TEXT & ~filters.COMMAND,adm_add_cont)]
    },
    fallbacks=[]
))
app.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_view_start, pattern="^ADM_VIEW$")],
    states={ ADMIN_SECTION:[CallbackQueryHandler(adm_view_sec,pattern=r"^AVS_")] },
    fallbacks=[]
))
app.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_del_start, pattern="^ADM_DEL$")],
    states={
      ADMIN_SECTION:[CallbackQueryHandler(adm_del_sec,pattern=r"^ADS_")],
      ADMIN_TITLE:[MessageHandler(filters.TEXT & ~filters.COMMAND,adm_del_id)]
    },
    fallbacks=[]
))
app.add_handler(ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_up_start, pattern="^ADM_UP$")],
    states={
      ADMIN_SECTION:[CallbackQueryHandler(adm_up_sec,pattern=r"^UPSEC_")],
      UPLOAD_FILE:[MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,adm_receive_file)]
    },
    fallbacks=[]
))

app.add_handler(CommandHandler("ai_chat", ai_chat_start))
app.add_handler(CommandHandler("stop_ai", ai_chat_stop))
app.add_handler(CommandHandler("ai_stats", ai_chat_stats))
app.add_handler(CallbackQueryHandler(ai_mode_select, pattern=r"^ai_mode_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_message))
app.add_handler(CommandHandler("tts", text_to_speech_start))
app.add_handler(CommandHandler("stop_tts", text_to_speech_stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_message))

app.run_polling()