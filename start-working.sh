#!/bin/bash
cd "$(dirname "$0")"

echo "🎭 Starting Working Seed-VC System..."

# Kill existing processes
pkill -f "uvicorn" || true
pkill -f "pnpm" || true
pkill -f "next" || true
sleep 2

# Free up ports
fuser -k 8000/tcp || true
fuser -k 3000/tcp || true
fuser -k 3001/tcp || true
sleep 1

# Start Redis
sudo systemctl start redis-server || true

# Create required directories
mkdir -p uploads outputs models logs

# Start backend
echo "🐍 Starting working backend..."
source venv/bin/activate
cd backend
python3 working_backend.py &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

# Wait for backend
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend started successfully on port 8000"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend on port 3001 to avoid conflicts
echo "🌐 Starting frontend on port 3001..."
PORT=3001 pnpm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid

# Wait for frontend
sleep 5

echo ""
echo "🎉 Working Seed-VC System Started!"
echo "=================================="
echo ""
echo "🌐 URLs:"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3001"
echo "Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo "API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "🧪 Test Commands:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:8000/test/voice-cloning"
echo "curl http://localhost:8000/models"
echo ""
echo "🎭 Voice Cloning Test:"
echo "curl http://localhost:8000/test/voice-cloning"
echo ""
echo "📊 Status:"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"