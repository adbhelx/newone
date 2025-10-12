
import json
import os
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Path to user achievement data files
USER_ACHIEVEMENTS_PREFIX = "user_achievements_"

def get_all_user_ids() -> List[int]:
    """Get a list of all user IDs who have achievement data files."""
    user_ids = []
    for filename in os.listdir('.'):
        if filename.startswith(USER_ACHIEVEMENTS_PREFIX) and filename.endswith('.json'):
            try:
                user_id_str = filename[len(USER_ACHIEVEMENTS_PREFIX):-len('.json')]
                user_ids.append(int(user_id_str))
            except ValueError:
                continue # Skip files with invalid user ID format
    return user_ids

def load_user_points(user_id: int) -> int:
    """Load total points for a specific user."""
    try:
        with open(f"{USER_ACHIEVEMENTS_PREFIX}{user_id}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("total_points", 0)
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
        # For now, we'll use a placeholder for username. 
        # In a real bot, you'd store usernames or fetch them if possible.
        # For simplicity, we'll just use user_id.
        leaderboard_data.append({"user_id": user_id, "points": points})

    # Sort by points in descending order
    leaderboard_data.sort(key=lambda x: x["points"], reverse=True)

    leaderboard_text = "🏆 **لوحة الصدارة** 🏆\n\n"
    if not leaderboard_data:
        leaderboard_text += "لا توجد بيانات في لوحة الصدارة بعد."
    else:
        for i, entry in enumerate(leaderboard_data):
            # Attempt to get username from context if available, otherwise use user_id
            # This is a simplification; a robust solution would store usernames.
            user_info = await context.bot.get_chat(entry["user_id"])
            username = user_info.username if user_info.username else f"User {entry["user_id"]}"
            
            if i == 0: # Gold medal for 1st place
                leaderboard_text += f"🥇 1. {username}: **{entry["points"]} نقطة**\n"
            elif i == 1: # Silver medal for 2nd place
                leaderboard_text += f"🥈 2. {username}: **{entry["points"]} نقطة**\n"
            elif i == 2: # Bronze medal for 3rd place
                leaderboard_text += f"🥉 3. {username}: **{entry["points"]} نقطة**\n"
            else:
                leaderboard_text += f"{i+1}. {username}: {entry["points"]} نقطة\n"
            
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

# Example usage in main.py:
"""
from leaderboard_feature import show_leaderboard

# Add to main_h handler
# if d == "MENU_LEADERBOARD":
#     return await show_leaderboard(update, context)

# Add button to main menu
# ("🏅 لوحة الصدارة", "MENU_LEADERBOARD"),
"""

