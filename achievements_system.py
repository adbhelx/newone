"""
نظام الإنجازات والشارات
Achievements & Badges System
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List

# Achievement definitions
ACHIEVEMENTS = {
    # Beginner achievements
    "first_steps": {
        "id": "first_steps",
        "name": "الخطوات الأولى",
        "name_en": "First Steps",
        "description": "أكمل أول درس",
        "icon": "👶",
        "points": 10,
        "condition": {"type": "lessons_completed", "value": 1}
    },
    "word_collector": {
        "id": "word_collector",
        "name": "جامع الكلمات",
        "name_en": "Word Collector",
        "description": "تعلم 50 كلمة جديدة",
        "icon": "📚",
        "points": 50,
        "condition": {"type": "words_learned", "value": 50}
    },
    
    # Consistency achievements
    "consistent_learner": {
        "id": "consistent_learner",
        "name": "المتعلم المثابر",
        "name_en": "Consistent Learner",
        "description": "سلسلة 7 أيام متتالية",
        "icon": "🔥",
        "points": 100,
        "condition": {"type": "streak_days", "value": 7}
    },
    "month_warrior": {
        "id": "month_warrior",
        "name": "محارب الشهر",
        "name_en": "Month Warrior",
        "description": "سلسلة 30 يوم متتالية",
        "icon": "⚡",
        "points": 500,
        "condition": {"type": "streak_days", "value": 30}
    },
    
    # Quiz achievements
    "quiz_master": {
        "id": "quiz_master",
        "name": "سيد الاختبارات",
        "name_en": "Quiz Master",
        "description": "احصل على 100% في 10 اختبارات",
        "icon": "🎯",
        "points": 200,
        "condition": {"type": "perfect_quizzes", "value": 10}
    },
    
    # Reading achievements
    "bookworm": {
        "id": "bookworm",
        "name": "دودة الكتب",
        "name_en": "Bookworm",
        "description": "اقرأ 50 قصة",
        "icon": "📖",
        "points": 150,
        "condition": {"type": "stories_read", "value": 50}
    },
    
    # HSK achievements
    "hsk1_master": {
        "id": "hsk1_master",
        "name": "خبير HSK1",
        "name_en": "HSK1 Master",
        "description": "أكمل جميع دروس HSK1",
        "icon": "🥉",
        "points": 300,
        "condition": {"type": "hsk_level_completed", "value": 1}
    },
    "hsk6_master": {
        "id": "hsk6_master",
        "name": "خبير HSK6",
        "name_en": "HSK6 Master",
        "description": "أكمل جميع دروس HSK6",
        "icon": "🏆",
        "points": 2000,
        "condition": {"type": "hsk_level_completed", "value": 6}
    },
    
    # Time achievements
    "dedicated_student": {
        "id": "dedicated_student",
        "name": "الطالب المجتهد",
        "name_en": "Dedicated Student",
        "description": "أمضِ 50 ساعة في التعلم",
        "icon": "⏰",
        "points": 400,
        "condition": {"type": "study_hours", "value": 50}
    },
    
    # Social achievements
    "helpful_friend": {
        "id": "helpful_friend",
        "name": "الصديق المساعد",
        "name_en": "Helpful Friend",
        "description": "ساعد 10 متعلمين آخرين",
        "icon": "🤝",
        "points": 250,
        "condition": {"type": "helped_users", "value": 10}
    },
    
    # Special achievements
    "early_bird": {
        "id": "early_bird",
        "name": "الطائر المبكر",
        "name_en": "Early Bird",
        "description": "تعلم قبل الساعة 7 صباحاً 10 مرات",
        "icon": "🌅",
        "points": 100,
        "condition": {"type": "early_sessions", "value": 10}
    },
    "night_owl": {
        "id": "night_owl",
        "name": "بومة الليل",
        "name_en": "Night Owl",
        "description": "تعلم بعد الساعة 11 مساءً 10 مرات",
        "icon": "🦉",
        "points": 100,
        "condition": {"type": "late_sessions", "value": 10}
    }
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

📊 المستوى: {level_info['icon']} {level_info['name_ar']} (المستوى {level_info['level']})
💎 النقاط: {level_info['points']}
🎯 التقدم للمستوى التالي: {level_info['progress']:.1f}%
🏅 الإنجازات: {unlocked_count}/{total_count}

📈 **الإحصائيات:**
• دروس مكتملة: {self.user_data['stats']['lessons_completed']}
• كلمات متعلمة: {self.user_data['stats']['words_learned']}
• سلسلة الأيام: {self.user_data['stats']['streak_days']} 🔥
• اختبارات كاملة: {self.user_data['stats']['perfect_quizzes']}
• قصص مقروءة: {self.user_data['stats']['stories_read']}
• ساعات الدراسة: {self.user_data['stats']['study_hours']:.1f}
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

{achievement['icon']} **{achievement['name']}**
{achievement['name_en']}

{achievement['description']}

💎 +{achievement['points']} نقطة
"""

# Example usage:
"""
# في bot.py
from achievements_system import AchievementSystem, format_achievement_notification

async def complete_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    achievement_system = AchievementSystem(user_id)
    
    # Update stat
    newly_unlocked = achievement_system.update_stat("lessons_completed", 1)
    
    # Notify user of new achievements
    for achievement in newly_unlocked:
        await update.message.reply_text(
            format_achievement_notification(achievement),
            parse_mode='Markdown'
        )
    
    # Show summary
    summary = achievement_system.get_achievement_summary()
    await update.message.reply_text(summary, parse_mode='Markdown')
"""
