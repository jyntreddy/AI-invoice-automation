#!/bin/bash

# Stop AI Invoice Automation Application

echo "🛑 Stopping AI Invoice Automation..."

# Kill processes on ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null

# Kill any remaining python/streamlit processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "streamlit run" 2>/dev/null

sleep 2

echo "✅ Application stopped"
