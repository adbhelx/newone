#!/bin/bash
# The Procfile handles the gunicorn web server which serves the webhook and health check
# The telegram bot is integrated into the Flask app (app_unified.py)
exec gunicorn app_unified:app --bind 0.0.0.0:"$PORT" --timeout 120
