"""
Enhanced Bot with AI Chat and Achievements
بوت محسّن مع المحادثة الذكية ونظام الإنجازات
"""

import os
import sys

# Add AI Chat and Achievements features
from ai_chat_feature import (
    ai_chat_start, ai_mode_select, ai_chat_message, 
    ai_chat_stop, ai_chat_stats
)
from achievements_system import AchievementSystem, format_achievement_notification

# Import original bot
import bot
from bot import *

# Override the main function to add new features
def main_enhanced():
    """Enhanced main function with AI and Achievements"""
    
    logger.info("Starting enhanced bot with AI Chat and Achievements...")
    
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # ===== ORIGINAL HANDLERS =====
    # Start and help
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Main menu
    app.add_handler(CallbackQueryHandler(show_section, pattern=r"^SEC_"))
    app.add_handler(CallbackQueryHandler(show_item, pattern=r"^ITEM_"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^BACK$"))
    
    # Admin panel
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^ADM_"))
    
    # Admin: Add content conversation
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_add_start, pattern="^ADM_ADD$"),
            CallbackQueryHandler(admin_add_section, pattern=r"^ADDSEC_")
        ],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_add_section, pattern=r"^ADDSEC_")],
            ADMIN_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_title)],
            ADMIN_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_content)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Admin: View content conversation
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_view_start, pattern="^ADM_VIEW$"),
            CallbackQueryHandler(admin_view_section, pattern=r"^VIEWSEC_")
        ],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_view_section, pattern=r"^VIEWSEC_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    
    # Admin: Delete content conversation
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_delete_start, pattern="^ADM_DEL$"),
            CallbackQueryHandler(admin_delete_section, pattern=r"^DELSEC_")
        ],
        states={
            ADMIN_SECTION: [CallbackQueryHandler(admin_delete_section, pattern=r"^DELSEC_")],
            ADMIN_DELETE_CONFIRM: [CallbackQueryHandler(admin_delete_confirm, pattern=r"^DELITEM_")]
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
    
    # ===== NEW FEATURES =====
    
    # AI Chat Feature
    app.add_handler(CommandHandler("ai_chat", ai_chat_start))
    app.add_handler(CommandHandler("stop_ai", ai_chat_stop))
    app.add_handler(CommandHandler("ai_stats", ai_chat_stats))
    app.add_handler(CallbackQueryHandler(ai_mode_select, pattern=r"^ai_mode_"))
    
    # Achievements Feature
    app.add_handler(CommandHandler("achievements", show_achievements))
    app.add_handler(CommandHandler("mystats", show_user_stats))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    
    # Message handler for AI chat (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Start polling
    logger.info("Enhanced bot is running with AI Chat and Achievements! 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


# ===== NEW COMMAND HANDLERS =====

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user achievements"""
    user_id = update.effective_user.id
    achievement_system = AchievementSystem(user_id)
    
    unlocked = achievement_system.get_unlocked_achievements()
    locked = achievement_system.get_locked_achievements()
    level_info = achievement_system.get_user_level()
    
    text = f"""
🏆 **إنجازاتك**

📊 المستوى: {level_info['icon']} {level_info['name_ar']} (المستوى {level_info['level']})
💎 النقاط: {level_info['points']}

✅ **الإنجازات المفتوحة** ({len(unlocked)}):
"""
    
    for ach in unlocked[:5]:  # Show first 5
        text += f"\n{ach['icon']} **{ach['name']}** - {ach['points']} نقطة"
    
    if len(unlocked) > 5:
        text += f"\n... و {len(unlocked) - 5} إنجاز آخر"
    
    text += f"\n\n🔒 **الإنجازات المقفلة** ({len(locked)}):"
    
    for ach in locked[:3]:  # Show first 3
        progress = ach.get('progress', 0)
        if isinstance(progress, bool):
            progress_text = "0%"
        else:
            progress_text = f"{progress:.0f}%"
        text += f"\n{ach['icon']} {ach['name']} - {progress_text}"
    
    text += "\n\n💡 استخدم /mystats لرؤية إحصائياتك الكاملة"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    achievement_system = AchievementSystem(user_id)
    
    summary = achievement_system.get_achievement_summary()
    await update.message.reply_text(summary, parse_mode='Markdown')


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global leaderboard"""
    # This would require a database to track all users
    # For now, show placeholder
    text = """
🏆 **لوحة الصدارة**

قريباً! سنضيف لوحة صدارة عامة لجميع المتعلمين.

في الوقت الحالي، استخدم:
• /mystats - لرؤية إحصائياتك
• /achievements - لرؤية إنجازاتك
"""
    await update.message.reply_text(text, parse_mode='Markdown')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages (for AI chat or achievements tracking)"""
    user_id = update.effective_user.id
    
    # Check if AI mode is active
    if "ai_mode" in context.user_data:
        await ai_chat_message(update, context)
        
        # Track achievement: used AI chat
        achievement_system = AchievementSystem(user_id)
        newly_unlocked = achievement_system.update_stat("ai_messages", 1)
        
        # Notify of new achievements
        for achievement in newly_unlocked:
            await update.message.reply_text(
                format_achievement_notification(achievement),
                parse_mode='Markdown'
            )
    else:
        # Regular message - could track as activity
        achievement_system = AchievementSystem(user_id)
        newly_unlocked = achievement_system.update_stat("messages_sent", 1)
        
        for achievement in newly_unlocked:
            await update.message.reply_text(
                format_achievement_notification(achievement),
                parse_mode='Markdown'
            )


if __name__ == "__main__":
    main_enhanced()

