#!/bin/bash

# Quick Commands for AI Invoice Automation

# Start the complete application (Backend + Frontend)
start_all() {
    echo "Starting complete application..."
    ./run_app.sh
}

# Start only backend
start_backend() {
    echo "Starting backend only..."
    source venv/bin/activate
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Start only frontend
start_frontend() {
    echo "Starting frontend only..."
    source venv/bin/activate
    streamlit run streamlit_app.py
}

# Stop all services
stop_all() {
    echo "Stopping all services..."
    ./stop_app.sh
}

# View logs
view_backend_logs() {
    tail -f backend.log
}

view_frontend_logs() {
    tail -f frontend.log
}

# Check status
check_status() {
    echo "Checking application status..."
    echo ""
    echo "Backend (Port 8000):"
    lsof -i:8000 || echo "  Not running"
    echo ""
    echo "Frontend (Port 8501):"
    lsof -i:8501 || echo "  Not running"
}

# Show help
show_help() {
    echo "AI Invoice Automation - Quick Commands"
    echo ""
    echo "Usage: source commands.sh && <command>"
    echo ""
    echo "Commands:"
    echo "  start_all          - Start backend + frontend"
    echo "  start_backend      - Start backend only"
    echo "  start_frontend     - Start frontend only"
    echo "  stop_all           - Stop all services"
    echo "  view_backend_logs  - View backend logs"
    echo "  view_frontend_logs - View frontend logs"
    echo "  check_status       - Check if services are running"
    echo ""
    echo "Direct scripts:"
    echo "  ./run_app.sh       - Start complete application"
    echo "  ./stop_app.sh      - Stop all services"
    echo ""
}

# If sourced, show help
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    show_help
fi
