
import os
from flask import Flask, request
from threading import Thread
import asyncio

# Import your bot's main function
from main import main as run_telegram_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running!"

@app.route('/health')
def health_check():
    return "OK"

def start_flask_app():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start Flask app in a separate thread
    flask_thread = Thread(target=start_flask_app)
    flask_thread.start()

    # Start Telegram bot in the main thread (or another thread if needed)
    # For python-telegram-bot v20+, it's an async function
    asyncio.run(run_telegram_bot())

