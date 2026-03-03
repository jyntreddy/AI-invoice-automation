#!/bin/bash

# AI Invoice Automation - Start Script
# This script starts both backend and frontend servers

echo "🚀 Starting AI Invoice Automation..."
echo ""

# Kill any existing processes on ports 8000 and 3000/3001
echo "📋 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null
sleep 2

# Start Backend
echo "🔧 Starting Backend API (http://localhost:8000)..."
cd "$(dirname "$0")"

# Check dependencies
echo "   Installing dependencies..."
pip install -q pydantic-settings loguru fastapi uvicorn sqlalchemy python-dotenv python-jose passlib 2>/dev/null

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 8

# Start Frontend
echo "🎨 Starting Frontend (http://localhost:3001)..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 5

echo ""
echo "✅ Services Started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Backend API:  http://localhost:8000"
echo "📍 API Docs:     http://localhost:8000/docs"
echo "📍 Frontend:     http://localhost:3001"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop: killall -9 uvicorn node"
echo ""

# Test backend
echo "🔍 Testing backend..."
sleep 2
HEALTH_CHECK=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Backend is responding!"
else
    echo "⚠️  Backend may still be starting..."
fi

echo ""
echo "🎉 Open http://localhost:3001 in your browser!"
