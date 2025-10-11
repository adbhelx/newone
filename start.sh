#!/bin/bash

# Start the enhanced bot with AI features in background
python bot_enhanced.py &

# Start the web app
gunicorn web_app:app --bind 0.0.0.0:$PORT

