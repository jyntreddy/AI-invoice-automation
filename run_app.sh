#!/bin/bash

# AI Invoice Automation - Complete Application Launcher
# This script starts both the FastAPI backend and Streamlit frontend

echo "🚀 Starting AI Invoice Automation System..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Kill any existing processes
echo "📋 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
sleep 2

# Start Backend API
echo "🔧 Starting Backend API (http://localhost:8000)..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "   Waiting for backend to initialize..."
sleep 8

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend is running"
else
    echo "   ⚠️  Backend may not be fully ready yet"
fi

# Start Frontend
echo ""
echo "🎨 Starting Streamlit Frontend (http://localhost:8501)..."
nohup streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 5

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📍 Access Points:"
echo "   Frontend (Streamlit):  http://localhost:8501"
echo "   Backend API:           http://localhost:8000"
echo "   API Documentation:     http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop the application:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or run: ./stop_app.sh"
echo ""
