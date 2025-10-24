from flask import Flask, render_template, jsonify, request
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data file
DB = "data.json"

def load_data():
    """Load data from JSON file"""
    try:
        if os.path.exists(DB):
            with open(DB, encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {}

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/sections')
def get_sections():
    """Get all sections with item counts"""
    data = load_data()
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
        "PictureDictionary": {"name": "معجم الصور", "icon": "📷", "category": "محتوى"},
        "GrammarTerms": {"name": "مصطلحات القواعد", "icon": "📝", "category": "محتوى"},
        "Proverbs": {"name": "الأمثال", "icon": "💭", "category": "محتوى"},
        "Applications": {"name": "التطبيقات", "icon": "📱", "category": "أدوات"}
    }
    
    for section_id, items in data.items():
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
    """Get items in a specific section"""
    data = load_data()
    items = data.get(section_id, [])
    
    return jsonify({
        "section": section_id,
        "items": items,
        "count": len(items)
    })

@app.route('/api/item/<section_id>/<int:item_id>')
def get_item(section_id, item_id):
    """Get a specific item"""
    data = load_data()
    items = data.get(section_id, [])
    item = next((x for x in items if x["id"] == item_id), None)
    
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    data = load_data()
    
    total_items = sum(len(items) for items in data.values())
    sections_with_content = sum(1 for items in data.values() if items)
    
    stats = {
        "total_sections": len(data),
        "sections_with_content": sections_with_content,
        "total_items": total_items,
        "last_updated": datetime.now().isoformat()
    }
    
    return jsonify(stats)

@app.route('/api/search')
def search():
    """Search for items"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    data = load_data()
    results = []
    
    for section_id, items in data.items():
        for item in items:
            if query in item["title"].lower() or query in str(item.get("content", "")).lower():
                results.append({
                    "section": section_id,
                    "item": item
                })
    
    return jsonify(results)

@app.route('/health')
def health():
    """Health check endpoint to keep the bot alive"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
