"""
ميزة المحادثة الذكية بالذكاء الاصطناعي
AI Chat Feature - أولوية عالية للتنفيذ
"""

import os
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Initialize Groq client (compatible with OpenAI API)
# Groq is FREE and FAST! 🚀
openai.api_key = os.environ.get("GROQ_API_KEY", "")
openai.api_base = "https://api.groq.com/openai/v1"

# System prompts for different modes
SYSTEM_PROMPTS = {
    "teacher": """أنت معلم لغة صينية محترف وصبور. 
    - ساعد المتعلم على تحسين لغته الصينية
    - صحح الأخطاء بلطف مع شرح السبب
    - قدم أمثلة عملية
    - استخدم العربية للشرح والصينية للأمثلة
    - كن مشجعاً ومحفزاً""",
    
    "conversation": """أنت صديق صيني يتحدث الصينية المبسطة.
    - تحدث بالصينية بشكل طبيعي
    - استخدم جمل بسيطة ومفهومة
    - أضف الترجمة العربية بين قوسين عند الحاجة
    - تحدث عن مواضيع يومية ممتعة""",
    
    "translator": """أنت مترجم محترف بين العربية والصينية.
    - ترجم بدقة وبشكل طبيعي
    - قدم ترجمات بديلة إن وجدت
    - اشرح السياق الثقافي عند الحاجة
    - قدم النطق بالبينيين (Pinyin)"""
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
        "translator": "🔤 وضع المترجم"
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
        
        # Call Groq API (FREE and FAST!)
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
