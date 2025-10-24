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
from datetime import datetime, time, timedelta
from typing import Dict, List
import random
from gtts import gTTS
import openai # Required for AI chat feature

# Configure logging for both Flask and Telegram Bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Content from config.py ---
TOKEN = "8085016643:AAEHAO1BlQzhdo39N7MSkx0NEZK3P0d5M58"  # ضع هنا التوكن الخاص بك
ADMIN_USER_IDS = [953696547, 7942066919]  # ضع هنا معرفات المستخدمين المشرفين

# Data file (from main.py)
DB = "data.json"
if os.path.exists(DB):
    with open(DB, encoding='utf-8') as f:
        data = json.load(f)
else:
    keys = [
        "HSK1","HSK2","HSK3","HSK4","HSK5","HSK6",
        "Quran","Dictionary","Stories","Gramnalessons","GrammarReview",
        "Dialogues","Flashcards","Quizzes","PictureDictionary","GrammarTerms","Proverbs",
        "Applications"
    ]
    data = {k: [] for k in keys}
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save():
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

# Conversation states (from main.py)
ADMIN_SECTION, ADMIN_TITLE, ADMIN_CONTENT, UPLOAD_FILE = range(4)


# --- Content from ai_chat_feature.py ---
"""
ميزة المحادثة الذكية بالذكاء الاصطناعي
AI Chat Feature - أولوية عالية للتنفيذ
"""
SYSTEM_PROMPTS = {
    "teacher": """أنت معلم لغة صينية محترف وصبور. \n    - ساعد المتعلم على تحسين لغته الصينية\n    - صحح الأخطاء بلطف مع شرح السبب\n    - قدم أمثلة عملية\n    - استخدم العربية للشرح والصينية للأمثلة\n    - كن مشجعاً ومحفزاً""",
    
    "conversation": """أنت صديق صيني يتحدث الصينية المبسطة.\n    - تحدث بالصينية بشكل طبيعي\n    - استخدم جمل بسيطة ومفهومة\n    - أضف الترجمة العربية بين قوسين عند الحاجة\n    - تحدث عن مواضيع يومية ممتعة""",
    
    "translator": """أنت مترجم محترف بين العربية والصينية.\n    - ترجم بدقة وبشكل طبيعي\n    - قدم ترجمات بديلة إن وجدت\n    - اشرح السياق الثقافي عند الحاجة\n    - قدم النطق بالبينيين (Pinyin)""",
    "academic_advisor": """أنت مستشار أكاديمي خبير في نظام التعليم السعودي (الابتدائي، المتوسط، الثانوي، الجامعي). مهمتك هي تقديم إجابات دقيقة ومفصلة ونصائح تحفيزية للطلاب حول مساراتهم التعليمية، وأفضل طرق الاستعداد لاختبارات القدرات والتحصيلي، وكيفية اختيار التخصصات الجامعية بما يتوافق مع رؤية 2030. استخدم لغة عربية فصحى ومحفزة."""
}

async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start AI chat conversation"""
    keyboard = [
        [
            InlineKeyboardButton("🎓 معلم", callback_data="ai_mode_teacher"),
            InlineKeyboardButton("💬 محادثة", callback_data="ai_mode_conversation")
        ],
        [
            InlineKeyboardButton("🔤 مترجم", callback_data="ai_mode_translator"),
            InlineKeyboardButton("🧑‍🏫 مرشد أكاديمي", callback_data="ai_mode_academic_advisor")
        ],
        [
            InlineKeyboardButton("❌ إلغاء", callback_data="ai_cancel")
        ]
    ]
    
    await update.message.reply_text(
        "🤖 **مرحباً بك في المحادثة الذكية!**\n\n"
        "اختر وضع المحادثة:\n\n"
        "🎓 **معلم**: للتعلم والتصحيح\n"
        "💬 **محادثة**: للممارسة الطبيعية\n"
        "🔤 **مترجم**: للترجمة الفورية",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ai_mode_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select AI chat mode"""
    query = update.callback_query
    await query.answer()
    
    mode = query.data.split("_")[-1]
    
    if mode == "cancel":
        await query.edit_message_text("تم إلغاء المحادثة الذكية.")
        return
    
    # Save mode in user context
    context.user_data["ai_mode"] = mode
    context.user_data["ai_history"] = []
    
    mode_names = {
        "teacher": "🎓 وضع المعلم",
        "conversation": "💬 وضع المحادثة", 
        "translator": "🔤 وضع المترجم",
        "academic_advisor": "🧑‍🏫 وضع المرشد الأكاديمي"
    }
    
    await query.edit_message_text(
        f"✅ تم اختيار {mode_names[mode]}\n\n"
        "ابدأ بإرسال رسالتك الآن!\n"
        "استخدم /stop_ai لإنهاء المحادثة."
    )

async def ai_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI chat messages"""
    # Check if AI mode is active
    if "ai_mode" not in context.user_data:
        return
    
    user_message = update.message.text
    mode = context.user_data["ai_mode"]
    history = context.user_data.get("ai_history", [])
    
    # Send typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Prepare messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS[mode]}
        ]
        
        # Add conversation history (last 10 messages)
        messages.extend(history[-10:])
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Update academic advisor usage count
        if mode == "academic_advisor":
            user_id = update.message.from_user.id
            achievement_system = AchievementSystem(user_id)
            achievement_system.increment_stat("academic_advisor_uses")
            
        # Call Groq API (compatible with OpenAI API)
        openai.api_key = os.environ.get("GROQ_API_KEY", "") # Ensure GROQ_API_KEY is set in Render environment variables
        openai.api_base = "https://api.groq.com/openai/v1"

        response = openai.ChatCompletion.create(
            model="llama-3.3-70b-versatile",  # Groq's free model
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Update history
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})
        context.user_data["ai_history"] = history
        
        # Send response
        await update.message.reply_text(ai_response, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ حدث خطأ في المحادثة: {str(e)}\n"
            "يرجى المحاولة مرة أخرى."
        )

async def ai_chat_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop AI chat"""
    if "ai_mode" in context.user_data:
        messages_count = len(context.user_data.get("ai_history", [])) // 2
        
        # Clear AI data
        context.user_data.pop("ai_mode", None)
        context.user_data.pop("ai_history", None)
        
        await update.message.reply_text(
            f"✅ تم إنهاء المحادثة الذكية.\n\n"
            f"📊 عدد الرسائل: {messages_count}\n\n"
            "استخدم /ai_chat للبدء من جديد."
        )
    else:
        await update.message.reply_text("لا توجد محادثة نشطة حالياً.")

async def ai_chat_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show AI chat statistics"""
    if "ai_mode" not in context.user_data:
        await update.message.reply_text("لا توجد محادثة نشطة حالياً.")
        return
    
    mode = context.user_data["ai_mode"]
    history = context.user_data.get("ai_history", [])
    messages_count = len(history) // 2
    
    mode_names = {
        "teacher": "🎓 وضع المعلم",
        "conversation": "💬 وضع المحادثة",
        "translator": "🔤 وضع المترجم"
    }
    
    await update.message.reply_text(
        f"📊 **إحصائيات المحادثة الحالية**\n\n"
        f"الوضع: {mode_names[mode]}\n"
        f"عدد الرسائل: {messages_count}\n"
        f"سجل المحادثة: {len(history)} رسالة\n\n"
        "استخدم /stop_ai لإنهاء المحادثة."
    )


# --- Content from achievements_system.py ---
"""
نظام الإنجازات والشارات
Achievements & Badges System
"""

# Achievement definitions
ACHIEVEMENTS = {
    "first_steps": {"id": "first_steps", "name": "الخطوات الأولى", "name_en": "First Steps", "description": "أكمل أول درس", "icon": "👶", "points": 10, "condition": {"type": "lessons_completed", "value": 1}},
    "word_collector": {"id": "word_collector", "name": "جامع الكلمات", "name_en": "Word Collector", "description": "تعلم 50 كلمة جديدة", "icon": "📚", "points": 50, "condition": {"type": "words_learned", "value": 50}},
    "consistent_learner": {"id": "consistent_learner", "name": "المتعلم المثابر", "name_en": "Consistent Learner", "description": "سلسلة 7 أيام متتالية", "icon": "🔥", "points": 100, "condition": {"type": "streak_days", "value": 7}},
    "month_warrior": {"id": "month_warrior", "name": "محارب الشهر", "name_en": "Month Warrior", "description": "سلسلة 30 يوم متتالية", "icon": "⚡", "points": 500, "condition": {"type": "streak_days", "value": 30}},
    "quiz_master": {"id": "quiz_master", "name": "سيد الاختبارات", "name_en": "Quiz Master", "description": "احصل على 100% في 10 اختبارات", "icon": "🎯", "points": 200, "condition": {"type": "perfect_quizzes", "value": 10}},
    "bookworm": {"id": "bookworm", "name": "دودة الكتب", "name_en": "Bookworm", "description": "اقرأ 50 قصة", "icon": "📖", "points": 150, "condition": {"type": "stories_read", "value": 50}},
        "hsk1_master": {"id": "hsk1_master", "name": "خبير HSK1", "name_en": "HSK1 Master", "description": "أكمل جميع دروس HSK1", "icon": "🥉", "points": 300, "condition": {"type": "hsk_level_completed", "value": 1}},
        "hsk6_master": {"id": "hsk6_master", "name": "خبير HSK6", "name_en": "HSK6 Master", "description": "أكمل جميع دروس HSK6", "icon": "🏆", "points": 2000, "condition": {"type": "hsk_level_completed", "value": 6}},
        "saudi_vision_2030": {"id": "saudi_vision_2030", "name": "نجم الرؤية 2030", "name_en": "Vision 2030 Star", "description": "استخدم المرشد الأكاديمي 10 مرات", "icon": "🇸🇦", "points": 500, "condition": {"type": "academic_advisor_uses", "value": 10}},
        "qiyas_pro": {"id": "qiyas_pro", "name": "متقن القياس", "name_en": "Qiyas Pro", "description": "أكمل 5 اختبارات قدرات/تحصيلي (وهمية)", "icon": "📝", "points": 750, "condition": {"type": "qiyas_quizzes_completed", "value": 5}},
    "dedicated_student": {"id": "dedicated_student", "name": "الطالب المجتهد", "name_en": "Dedicated Student", "description": "أمضِ 50 ساعة في التعلم", "icon": "⏰", "points": 400, "condition": {"type": "study_hours", "value": 50}},
    "helpful_friend": {"id": "helpful_friend", "name": "الصديق المساعد", "name_en": "Helpful Friend", "description": "ساعد 10 متعلمين آخرين", "icon": "🤝", "points": 250, "condition": {"type": "helped_users", "value": 10}},
    "early_bird": {"id": "early_bird", "name": "الطائر المبكر", "name_en": "Early Bird", "description": "تعلم قبل الساعة 7 صباحاً 10 مرات", "icon": "🌅", "points": 100, "condition": {"type": "early_sessions", "value": 10}},
    "night_owl": {"id": "night_owl", "name": "بومة الليل", "name_en": "Night Owl", "description": "تعلم بعد الساعة 11 مساءً 10 مرات", "icon": "🦉", "points": 100, "condition": {"type": "late_sessions", "value": 10}}
}

class AchievementSystem:
    """Achievement tracking and management system"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_data = self.load_user_data()
    
    def load_user_data(self) -> Dict:
        """Load user achievement data"""
        try:
            with open(f"user_achievements_{self.user_id}.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "unlocked_achievements": [],
                "progress": {},
                "total_points": 0,
                "stats": {
                    "lessons_completed": 0,
                    "words_learned": 0,
                    "streak_days": 0,
                    "perfect_quizzes": 0,
                    "stories_read": 0,
                    "study_hours": 0,
                    "helped_users": 0,
                    "early_sessions": 0,
                    "late_sessions": 0,
                    "hsk_levels_completed": []
                }
            }
    
    def save_user_data(self):
        """Save user achievement data"""
        with open(f"user_achievements_{self.user_id}.json", 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=2)
    
    def update_stat(self, stat_name: str, value: int = 1):
        """Update a user statistic"""
        if stat_name in self.user_data["stats"]:
            if isinstance(self.user_data["stats"][stat_name], list):
                if value not in self.user_data["stats"][stat_name]:
                    self.user_data["stats"][stat_name].append(value)
            else:
                self.user_data["stats"][stat_name] += value
            
            self.save_user_data()
            return self.check_achievements()
        return []
    
    def check_achievements(self) -> List[Dict]:
        """Check for newly unlocked achievements"""
        newly_unlocked = []
        
        for achievement_id, achievement in ACHIEVEMENTS.items():
            # Skip if already unlocked
            if achievement_id in self.user_data["unlocked_achievements"]:
                continue
            
            # Check condition
            condition = achievement["condition"]
            stat_value = self.user_data["stats"].get(condition["type"], 0)
            
            # Handle different condition types
            if condition["type"] == "hsk_level_completed":
                if condition["value"] in stat_value:
                    newly_unlocked.append(achievement)
                    self.unlock_achievement(achievement_id)
            else:
                if isinstance(stat_value, (int, float)) and stat_value >= condition["value"]:
                    newly_unlocked.append(achievement)
                    self.unlock_achievement(achievement_id)
        
        return newly_unlocked
    
    def unlock_achievement(self, achievement_id: str):
        """Unlock an achievement"""
        if achievement_id not in self.user_data["unlocked_achievements"]:
            self.user_data["unlocked_achievements"].append(achievement_id)
            achievement = ACHIEVEMENTS[achievement_id]
            self.user_data["total_points"] += achievement["points"]
            self.save_user_data()
    
    def get_user_level(self) -> Dict:
        """Calculate user level based on points"""
        points = self.user_data["total_points"]
        
        # Level thresholds
        levels = [
            (0, "مبتدئ", "Beginner", "🌱"),
            (100, "متعلم", "Learner", "🌿"),
            (500, "متقدم", "Advanced", "🌳"),
            (1000, "خبير", "Expert", "⭐"),
            (2000, "محترف", "Professional", "💎"),
            (5000, "أسطورة", "Legend", "👑")
        ]
        
        for i, (threshold, name_ar, name_en, icon) in enumerate(levels):
            if i == len(levels) - 1 or points < levels[i + 1][0]:
                next_threshold = levels[i + 1][0] if i < len(levels) - 1 else None
                return {
                    "level": i + 1,
                    "name_ar": name_ar,
                    "name_en": name_en,
                    "icon": icon,
                    "points": points,
                    "next_level_points": next_threshold,
                    "progress": ((points - threshold) / (next_threshold - threshold) * 100) if next_threshold else 100
                }
        
        return levels[0]
    
    def get_achievement_summary(self) -> str:
        """Get formatted achievement summary"""
        level_info = self.get_user_level()
        unlocked_count = len(self.user_data["unlocked_achievements"])
        total_count = len(ACHIEVEMENTS)
        
        summary = f"""
🏆 **ملخص الإنجازات**

📊 المستوى: {level_info["icon"]} {level_info["name_ar"]} (المستوى {level_info["level"]})
💎 النقاط: {level_info["points"]}
🎯 التقدم للمستوى التالي: {level_info["progress"]:.1f}%
🏅 الإنجازات: {unlocked_count}/{total_count}

📈 **الإحصائيات:**
• دروس مكتملة: {self.user_data["stats"]["lessons_completed"]}
• كلمات متعلمة: {self.user_data["stats"]["words_learned"]}
• سلسلة الأيام: {self.user_data["stats"]["streak_days"]}
• اختبارات كاملة: {self.user_data["stats"]["perfect_quizzes"]}
• قصص مقروءة: {self.user_data["stats"]["stories_read"]}
• ساعات الدراسة: {self.user_data["stats"]["study_hours"]:.1f}
"""
        return summary
    
    def get_unlocked_achievements(self) -> List[Dict]:
        """Get list of unlocked achievements"""
        return [
            ACHIEVEMENTS[aid] 
            for aid in self.user_data["unlocked_achievements"]
        ]
    
    def get_locked_achievements(self) -> List[Dict]:
        """Get list of locked achievements with progress"""
        locked = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            if achievement_id not in self.user_data["unlocked_achievements"]:
                condition = achievement["condition"]
                current = self.user_data["stats"].get(condition["type"], 0)
                
                if condition["type"] == "hsk_level_completed":
                    progress = condition["value"] in current
                else:
                    progress = (current / condition["value"] * 100) if condition["value"] > 0 else 0
                
                achievement_copy = achievement.copy()
                achievement_copy["progress"] = progress
                achievement_copy["current"] = current
                achievement_copy["target"] = condition["value"]
                locked.append(achievement_copy)
        
        return sorted(locked, key=lambda x: x["progress"], reverse=True)

def format_achievement_notification(achievement: Dict) -> str:
    """Format achievement unlock notification"""
    return f"""
🎉 **إنجاز جديد مفتوح!**

{achievement["icon"]} **{achievement["name"]}**
{achievement["name_en"]}

{achievement["description"]}

💎 +{achievement["points"]} نقطة
"""

# --- Achievement Handlers (moved outside class for direct use) ---
async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    ach_system = AchievementSystem(user_id)
    summary = ach_system.get_achievement_summary()

    keyboard = [
        [InlineKeyboardButton("✅ إنجازات مفتوحة", callback_data="ACH_UNLOCKED")],
        [InlineKeyboardButton("🔒 إنجازات مغلقة", callback_data="ACH_LOCKED")],
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')

async def show_unlocked_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    ach_system = AchievementSystem(user_id)
    unlocked = ach_system.get_unlocked_achievements()

    if not unlocked:
        await query.edit_message_text("لا توجد إنجازات مفتوحة بعد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_ACHIEVEMENTS")]]))
        return

    text = "✅ **إنجازاتك المفتوحة:**\n\n"
    for ach in unlocked:
        text += f"{ach["icon"]} **{ach["name"]}** - {ach["description"]}\n"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_ACHIEVEMENTS")]]), parse_mode='Markdown')

async def show_locked_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    ach_system = AchievementSystem(user_id)
    locked = ach_system.get_locked_achievements()

    if not locked:
        await query.edit_message_text("لقد فتحت جميع الإنجازات! رائع!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_ACHIEVEMENTS")]]))
        return

    text = "🔒 **إنجازاتك المغلقة:**\n\n"
    for ach in locked:
        progress_bar = "⬜" * (ach["progress"] // 10) + "⬛" * (10 - (ach["progress"] // 10))
        text += f"{ach["icon"]} **{ach["name"]}**\n"
        text += f"  {ach["description"]}\n"
        if isinstance(ach["current"], list):
            text += f"  التقدم: {len(ach["current"])} / {ach["target"]}\n\n"
        else:
            text += f"  التقدم: {ach["current"]}/{ach["target"]} ({ach["progress"]:.1f}%)\n\n"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="MENU_ACHIEVEMENTS")]]), parse_mode='Markdown')


# --- Content from text_to_speech_feature.py ---

async def text_to_speech_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start text-to-speech feature"""
    keyboard = [
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    await update.message.reply_text(
        """🔊 **ميزة النطق الصوتي!**\n\n"
        "أرسل لي أي نص صيني وسأقوم بنطقه لك.\n"
        "استخدم /stop_tts لإنهاء هذه الميزة.""",
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


# --- Content from daily_reminders_feature.py ---

REMINDERS_DB = "user_reminders.json"

def load_reminders():
    if os.path.exists(REMINDERS_DB):
        with open(REMINDERS_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_reminders(reminders):
    with open(REMINDERS_DB, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

async def send_daily_reminder_message(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    user_id = job_data["user_id"]
    chat_id = job_data["chat_id"]

    message = (
        """🔔 **تذكيرك اليومي لتعلم الصينية!**\n\n"
        "حان وقت الدراسة! إليك كلمة اليوم:\n"
        "**你好 (Nǐ hǎo) - مرحباً**\n\n"
        "استمر في التقدم! 🚀"""
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def start_reminders_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⏰ 09:00 صباحاً", callback_data="set_reminder_0900")],
        [InlineKeyboardButton("⏰ 13:00 ظهراً", callback_data="set_reminder_1300")],
        [InlineKeyboardButton("⏰ 20:00 مساءً", callback_data="set_reminder_2000")],
        [InlineKeyboardButton("❌ إلغاء التذكير", callback_data="cancel_reminder")],
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    await update.message.reply_text(
        """🔔 **تذكيرات يومية ذكية!**\n\n"
        "اختر الوقت الذي تفضل أن أذكرك فيه بالدراسة:\n"
        "(يمكنك إلغاء التذكير في أي وقت)""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def set_daily_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if query.data == "cancel_reminder":
        reminders = load_reminders()
        if str(user_id) in reminders:
            if reminders[str(user_id)].get("job_name"):
                current_jobs = context.job_queue.get_jobs_by_name(reminders[str(user_id)]["job_name"])
                for job in current_jobs:
                    job.schedule_removal()
            reminders.pop(str(user_id))
            save_reminders(reminders)
            await query.edit_message_text("✅ تم إلغاء التذكير اليومي بنجاح.")
        else:
            await query.edit_message_text("لا يوجد تذكير يومي نشط لإلغائه.")
        return

    selected_time_str = query.data.split("_")[-1]
    hour = int(selected_time_str[:2])
    minute = int(selected_time_str[2:])
    reminder_time = time(hour, minute)

    job_name = f"daily_reminder_{user_id}"

    # Remove existing job if any
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()

    # Schedule new job
    context.job_queue.run_daily(
        send_daily_reminder_message,
        reminder_time,
        days=(0, 1, 2, 3, 4, 5, 6), # Every day
        chat_id=chat_id,
        name=job_name,
        data={
            "user_id": user_id,
            "chat_id": chat_id,
            "time": selected_time_str
        }
    )

    reminders = load_reminders()
    reminders[str(user_id)] = {"time": selected_time_str, "chat_id": chat_id, "job_name": job_name}
    save_reminders(reminders)

    await query.edit_message_text(
        f"✅ تم تعيين تذكير يومي في الساعة {hour:02d}:{minute:02d}.\n"
        "سأرسل لك كلمة اليوم أو تحديًا بسيطًا."
    )

async def re_schedule_all_reminders(application):
    reminders = load_reminders()
    for user_id_str, reminder_info in reminders.items():
        user_id = int(user_id_str)
        chat_id = reminder_info["chat_id"]
        selected_time_str = reminder_info["time"]
        job_name = reminder_info["job_name"]

        hour = int(selected_time_str[:2])
        minute = int(selected_time_str[2:])
        reminder_time = time(hour, minute)

        application.job_queue.run_daily(
            send_daily_reminder_message,
            reminder_time,
            days=(0, 1, 2, 3, 4, 5, 6),
            chat_id=chat_id,
            name=job_name,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "time": selected_time_str
            }
        )
        print(f"Rescheduled reminder for user {user_id} at {reminder_time}")


# --- Content from word_matching_game.py ---

SELECTING_ANSWER = 0 # Conversation state

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


# --- Content from leaderboard_feature.py ---

USER_ACHIEVEMENTS_PREFIX = "user_achievements_"

def get_all_user_ids() -> List[int]:
    """Get a list of all user IDs who have achievement data files."""
    user_ids = []
    for filename in os.listdir("."):
        if filename.startswith(USER_ACHIEVEMENTS_PREFIX) and filename.endswith(".json"):
            try:
                user_id_str = filename[len(USER_ACHIEVEMENTS_PREFIX):-len(".json")]
                user_ids.append(int(user_id_str))
            except ValueError:
                continue # Skip files with invalid user ID format
    return user_ids

def load_user_points(user_id: int) -> int:
    """Load total points for a specific user."""
    try:
        # Load achievement data for the user and return total_points
        with open(f"{USER_ACHIEVEMENTS_PREFIX}{user_id}.json", "r", encoding="utf-8") as f:
            user_ach_data = json.load(f)
            return user_ach_data.get("total_points", 0)
    except FileNotFoundError:
        return 0
    except json.JSONDecodeError:
        return 0

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the leaderboard."""
    query = update.callback_query
    if query:
        await query.answer()

    all_user_ids = get_all_user_ids()
    leaderboard_data = []

    for user_id in all_user_ids:
        points = load_user_points(user_id)
        username = f"User {user_id}" # Placeholder
        try:
            user_info = await context.bot.get_chat(user_id)
            if user_info.username:
                username = f"@{user_info.username}"
            elif user_info.first_name:
                username = user_info.first_name
        except Exception as e:
            print(f"Could not fetch user info for {user_id}: {e}")
            
        leaderboard_data.append({"user_id": user_id, "points": points, "username": username})

    # Sort by points in descending order
    leaderboard_data.sort(key=lambda x: x["points"], reverse=True)

    leaderboard_text = "🏆 **لوحة الصدارة** 🏆\n\n"
    if not leaderboard_data:
        leaderboard_text += "لا توجد بيانات في لوحة الصدارة بعد."
    else:
        for i, entry in enumerate(leaderboard_data):
            
            if i == 0: # Gold medal for 1st place
                leaderboard_text += f"🥇 1. {entry['username']}: **{entry['points']} نقطة**\n"
            elif i == 1: # Silver medal for 2nd place
                leaderboard_text += f"🥈 2. {entry['username']}: **{entry['points']} نقطة**\n"
            elif i == 2: # Bronze medal for 3rd place
                leaderboard_text += f"🥉 3. {entry['username']}: **{entry['points']} نقطة**\n"
            else:
                leaderboard_text += f"{i+1}. {entry['username']}: {entry['points']} نقطة\n"
            
            if i >= 9: # Show top 10 only
                break

    keyboard = [
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(leaderboard_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown', reply_markup=reply_markup)


# --- Content from main.py (core bot logic) ---

# Build main keyboard
def build_main_menu():
    items = [
        ("📚 التعليم المخصص", "MENU_CUSTOM_EDU"),
        ("🕌 القرآن", "SKIP_Quran"),
        ("🗂️ القاموس", "SKIP_Dictionary"),
        ("📖 القصص", "SKIP_Stories"),
        ("🔤 قواعد", "SKIP_GrammarLessons"),
        ("📑 مراجعة", "SKIP_GrammarReview"),
        ("💬 محادثات", "SKIP_Dialogues"),
        ("🃏 Flashcards", "SKIP_Flashcards"),
        ("❓ كويزات", "SKIP_Quizzes"),
        ("📷 معجم صور", "SKIP_PictureDictionary"),
        ("🧑‍🏫 مرشد أكاديمي", "MENU_ACADEMIC_ADVISOR"),
        ("🤖 AI Chat", "MENU_AI_CHAT"),
        ("🏆 الإنجازات", "MENU_ACHIEVEMENTS"),
        ("🔊 نطق صوتي", "MENU_TTS"),
        ("🔔 تذكيرات", "MENU_REMINDERS"),
        ("🎮 لعبة كلمات", "MENU_WORD_GAME"),
        ("🏅 لوحة الصدارة", "MENU_LEADERBOARD"),
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
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="BACK")])
        return await q.edit_message_text("قسم التطبيقات:", reply_markup=InlineKeyboardMarkup(kb))

    # Custom Education Menu
    if d == "MENU_CUSTOM_EDU":
        kb = [
            [InlineKeyboardButton("📚 مناهج STEM", callback_data="SKIP_STEM")],
            [InlineKeyboardButton("💡 مهارات التفكير النقدي", callback_data="SKIP_CRITICAL_THINKING")],
            [InlineKeyboardButton("📝 اختبارات القدرات والتحصيلي", callback_data="SKIP_TESTS")],
            [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
        ]
        return await q.edit_message_text("اختر قسم التعليم المخصص:", reply_markup=InlineKeyboardMarkup(kb))

    # Academic Advisor shortcut
    if d == "MENU_ACADEMIC_ADVISOR":
        # Note: This will trigger the AI Chat start and select the mode automatically
        context.user_data["ai_mode"] = "academic_advisor"
        context.user_data["ai_history"] = []
        await q.edit_message_text(
            "✅ تم تفعيل وضع المرشد الأكاديمي.\n\n"
            "اسأل عن التخصصات، اختبارات القدرات، أو أي نصيحة دراسية!\n"
            "استخدم /stop_ai لإنهاء المحادثة."
        )
        return

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

    # Daily Reminders
    if d == "MENU_REMINDERS":
        return await start_reminders_setup(update, context)

    # Word Game
    if d == "MENU_WORD_GAME":
        return await start_word_matching_game(update, context)

    # Leaderboard
    if d == "MENU_LEADERBOARD":
        return await show_leaderboard(update, context)

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
async def view_i(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, sec, sid = q.data.split("_")
    idx = int(sid)
    itm = next((x for x in data.get(sec, []) if x['id'] == idx), None)
    if not itm:
        return await q.edit_message_text("⚠️ غير موجود.")
    await q.message.reply_document(document=itm['content'], filename=itm['title'])
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
    context.user_data['sec'] = q.data.split("_", 1)[1]
    await q.edit_message_text("✏️ أرسل عنوان العنصر:")
    return ADMIN_TITLE

async def adm_add_title(update: Update, context):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("🌐 أرسل محتوى (نص أو رابط أو file_id):")
    return ADMIN_CONTENT

async def adm_add_cont(update: Update, context):
    sec = context.user_data['sec']
    title = context.user_data['title']
    content = update.message.text.strip()
    nid = max([x['id'] for x in data[sec]] or [0]) + 1
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
    context.user_data['sec'] = q.data.split("_", 1)[1]
    lst = "\n".join(f"- {i['title']} (id={i['id']})" for i in data[context.user_data['sec']])
    await q.edit_message_text(f"أرسل ID العنصر لحذفه من {context.user_data['sec']}:\n{lst}")
    return ADMIN_TITLE

async def adm_del_id(update: Update, context):
    sec = context.user_data['sec']
    try:
        idx = int(update.message.text)
    except:
        await update.message.reply_text("⚠️ id خاطئ.")
        return ADMIN_TITLE
    before = len(data[sec])
    data[sec] = [x for x in data[sec] if x['id'] != idx]
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
    context.user_data['sec'] = q.data.split("_", 1)[1]
    await q.edit_message_text(f"✏️ أرسل الملف للقسم {context.user_data['sec']}:")
    return UPLOAD_FILE

async def adm_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    sec = context.user_data['sec']
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

    nid = max([x['id'] for x in data[sec]] or [0]) + 1
    data[sec].append({"id": nid, "title": name, "content": fid})
    save()
    await msg.reply_text(f"✅ تم حفظ الملف في {sec}:\n`{name}`\nfile_id=`{fid}`", parse_mode='Markdown')
    return ConversationHandler.END

# 5) Edit item
async def adm_edit_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton(sec, callback_data=f"AES_{sec}")] for sec in data.keys()]
    kb.append([InlineKeyboardButton("◀️ رجوع", callback_data="MENU_Admin")])
    await q.edit_message_text("اختر القسم لتعديل عنصر منه:", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_SECTION

async def adm_edit_sec(update: Update, context):
    q = update.callback_query
    await q.answer()
    context.user_data['sec'] = q.data.split("_", 1)[1]
    lst = "\n".join(f"- {i['title']} (id={i['id']})" for i in data[context.user_data['sec']])
    await q.edit_message_text(f"اختر العنصر للتعديل من {context.user_data['sec']}:\n{lst}", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(item['title'], callback_data=f"AEI_{item['id']}")] for item in data[context.user_data['sec']]] +
        [[InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]]
    ))
    return ADMIN_TITLE

async def adm_edit_item(update: Update, context):
    q = update.callback_query
    await q.answer()
    item_id = int(q.data.split("_", 1)[1])
    sec = context.user_data['sec']
    item = next((x for x in data.get(sec, []) if x['id'] == item_id), None)
    if not item:
        await q.edit_message_text("⚠️ العنصر غير موجود.")
        return ConversationHandler.END

    context.user_data['editing_item'] = item
    context.user_data['editing_item_id'] = item_id

    kb = [
        [InlineKeyboardButton(f"تعديل العنوان: {item['title']}", callback_data=f"AEC_TITLE_{item_id}")],
        [InlineKeyboardButton(f"تعديل المحتوى: {item['content']}", callback_data=f"AEC_CONT_{item_id}")],
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    await q.edit_message_text(f"ماذا تريد أن تعدل في العنصر (ID: {item_id}) من القسم {sec}?", reply_markup=InlineKeyboardMarkup(kb))
    return ADMIN_CONTENT

async def adm_edit_cont_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("✏️ أرسل المحتوى الجديد:")
    return ADMIN_CONTENT

async def adm_edit_cont(update: Update, context):
    sec = context.user_data['sec']
    item_id = context.user_data['editing_item_id']
    new_content = update.message.text.strip()

    for item in data[sec]:
        if item['id'] == item_id:
            item['content'] = new_content
            break
    save()
    await update.message.reply_text(f"✅ تم تحديث محتوى العنصر (ID: {item_id}) في {sec}.")
    return ConversationHandler.END

async def adm_edit_title_start(update: Update, context):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("✏️ أرسل العنوان الجديد:")
    return ADMIN_CONTENT

async def adm_edit_title(update: Update, context):
    sec = context.user_data['sec']
    item_id = context.user_data['editing_item_id']
    new_title = update.message.text.strip()

    for item in data[sec]:
        if item['id'] == item_id:
            item['title'] = new_title
            break
    save()
    await update.message.reply_text(f"✅ تم تحديث عنوان العنصر (ID: {item_id}) في {sec}.")
    return ConversationHandler.END


# Flask App Setup
app = Flask(__name__)

# Telegram Bot Setup
application = ApplicationBuilder().token(TOKEN).build()
# application.initialize() # تم إزالته لأنه غير ضروري ويسبب تحذيرات
logger.info("Telegram bot Application initialized.")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(main_h, pattern="^(MENU_|BACK|SKIP_|SEC_)"))

# AI Chat handlers
application.add_handler(CallbackQueryHandler(ai_chat_start, pattern="^MENU_AI_CHAT$"))
application.add_handler(CallbackQueryHandler(ai_mode_select, pattern="^ai_mode_"))
application.add_handler(CommandHandler("stop_ai", ai_chat_stop))
application.add_handler(CommandHandler("ai_stats", ai_chat_stats))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_message))

# Achievements handlers (ensure these are defined before this section)
application.add_handler(CallbackQueryHandler(show_achievements, pattern="^MENU_ACHIEVEMENTS$"))
application.add_handler(CallbackQueryHandler(show_unlocked_achievements, pattern="^ACH_UNLOCKED$"))
application.add_handler(CallbackQueryHandler(show_locked_achievements, pattern="^ACH_LOCKED$"))
application.add_handler(CallbackQueryHandler(show_achievements, pattern="^MENU_ACHIEVEMENTS")) # Added for BACK from achievements

# Text-to-Speech handlers
application.add_handler(CallbackQueryHandler(text_to_speech_start, pattern="^MENU_TTS$"))
application.add_handler(CommandHandler("stop_tts", text_to_speech_stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_message))

# Daily Reminders handlers
application.add_handler(CallbackQueryHandler(start_reminders_setup, pattern="^MENU_REMINDERS$"))
application.add_handler(CallbackQueryHandler(set_daily_reminder, pattern="^set_reminder_|^cancel_reminder$"))

# Word Matching Game handlers
word_matching_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_word_matching_game, pattern="^MENU_WORD_GAME$")],
    states={
        SELECTING_ANSWER: [
            CallbackQueryHandler(check_answer, pattern=r"^game_answer_"),
            CallbackQueryHandler(end_word_matching_game, pattern="^game_end$")
        ]
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(word_matching_conv_handler)

# Leaderboard handler
application.add_handler(CallbackQueryHandler(show_leaderboard, pattern="^MENU_LEADERBOARD$"))

application.add_handler(CallbackQueryHandler(view_i, pattern="^VIEW_"))

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
        ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, adm_del_id)]
    },
    fallbacks=[CallbackQueryHandler(main_h, pattern="^BACK$")]
)
application.add_handler(conv_handler_del)

conv_handler_up = ConversationHandler(
    entry_points=[CallbackQueryHandler(adm_up_start, pattern="^ADM_UP$")],
    states={
        ADMIN_SECTION: [CallbackQueryHandler(adm_up_sec, pattern="^UPSEC_")],
        UPLOAD_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, adm_receive_file)]
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

# Flask Routes for Web App (from web_app.py)
app = Flask(__name__)

@app.route('/')
def index():
    # In a real scenario, you might serve a simple HTML page or redirect to bot info
    return "Hello from Flask! Your bot is running."

@app.route('/webhook', methods=['POST'])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    # Run the update processing in a separate task to avoid blocking the Flask thread
    asyncio.create_task(application.process_update(update))
    return 'ok'

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
    item = next((x for x in items if x['id'] == item_id), None)
    
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
            if query in item['title'].lower() or query in str(item.get("content", "")).lower():
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
def run_bot_thread_target(app_instance):
    logger.info("Telegram bot thread target started.")
    # Run the reminder rescheduling in the bot's event loop
    asyncio.run(re_schedule_all_reminders(app_instance))
    logger.info("Telegram bot reminders rescheduled.")
    # The bot doesn't need to run_polling() or run_webhook() here,
    # as Flask handles incoming webhooks and passes them to application.process_update()

# Start the Telegram bot in a separate thread
# This thread will manage the bot\'s background tasks (like job_queue and webhook setup)
telegram_bot_thread = threading.Thread(target=run_bot_thread_target, args=(application,))
telegram_bot_thread.daemon = True # Allow main program to exit even if thread is running

# Start the bot thread globally, outside of if __name__ == '__main__':
# This ensures it runs when gunicorn imports the module
telegram_bot_thread.start()
logger.info("Telegram bot thread started.")

if __name__ == '__main__':
    # Run Flask app only if executed directly
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Flask app starting on port {port}")
    app.run(host="0.0.0.0", port=port)
