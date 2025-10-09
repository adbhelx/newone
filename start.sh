#!/bin/bash

# Start the bot in background
python bot.py &

# Start the web app
gunicorn web_app:app --bind 0.0.0.0:$PORT
