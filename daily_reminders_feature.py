
import json
import os
from datetime import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

REMINDERS_DB = "user_reminders.json"

def load_reminders():
    if os.path.exists(REMINDERS_DB):
        with open(REMINDERS_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_reminders(reminders):
    with open(REMINDERS_DB, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

async def start_reminders_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⏰ 09:00 صباحاً", callback_data="set_reminder_0900")],
        [InlineKeyboardButton("⏰ 13:00 ظهراً", callback_data="set_reminder_1300")],
        [InlineKeyboardButton("⏰ 20:00 مساءً", callback_data="set_reminder_2000")],
        [InlineKeyboardButton("❌ إلغاء التذكير", callback_data="cancel_reminder")],
        [InlineKeyboardButton("◀️ رجوع", callback_data="BACK")]
    ]
    await update.message.reply_text(
        "🔔 **تذكيرات يومية ذكية!**\n\n"
        "اختر الوقت الذي تفضل أن أذكرك فيه بالدراسة:\n"
        "(يمكنك إلغاء التذكير في أي وقت)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=\'Markdown\'
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

async def send_daily_reminder_message(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    user_id = job_data["user_id"]
    chat_id = job_data["chat_id"]

    # Here you can customize the reminder message
    # For example, send a 'word of the day' or a simple challenge
    message = (
        "🔔 **تذكيرك اليومي لتعلم الصينية!**\n\n"
        "حان وقت الدراسة! إليك كلمة اليوم:\n"
        "**你好 (Nǐ hǎo) - مرحباً**\n\n"
        "استمر في التقدم! 🚀"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=\'Markdown\')

# Function to re-schedule reminders on bot restart
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

# Example usage in main.py:
"""
from daily_reminders_feature import (
    start_reminders_setup, set_daily_reminder, re_schedule_all_reminders
)

# Add handlers
app.add_handler(CommandHandler("remind", start_reminders_setup))
app.add_handler(CallbackQueryHandler(set_daily_reminder, pattern=r"^set_reminder_|^cancel_reminder"))

# Call this after app.run_polling() or at bot startup
# application.post_init(re_schedule_all_reminders)
"""

