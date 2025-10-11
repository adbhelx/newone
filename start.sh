#!/bin/bash

# Start the original bot in background (without AI features to avoid errors)
python bot.py &

# Start the web app
gunicorn web_app:app --bind 0.0.0.0:$PORT

