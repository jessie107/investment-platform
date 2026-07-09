#!/bin/bash
# Start the Investment Research & Screening Platform
# Usage: ./start.sh

echo "🚀 Starting InvestScreen Platform..."
echo ""

# Start backend
echo "📦 Starting backend..."
cd "$(dirname "$0")/backend"
/usr/local/bin/python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "🎨 Starting frontend..."
cd "$(dirname "$0")/frontend"
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "✅ InvestScreen is running!"
echo "   Frontend: http://localhost:5173"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo ""
echo "   Demo login: demo@invest.com / demo123"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
