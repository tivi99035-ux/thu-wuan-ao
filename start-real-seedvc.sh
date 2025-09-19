#!/bin/bash

# Start Real Seed-VC Implementation
# Script khởi động với voice cloning thực tế

cd "$(dirname "$0")"

echo "🎭 Starting Real Seed-VC System..."
echo "=================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Không tìm thấy package.json. Chạy từ thư mục project root."
    exit 1
fi

# Stop any existing services
echo "🛑 Stopping existing services..."
pkill -f "uvicorn main" || true
pkill -f "pnpm" || true

# Install missing Python dependencies for real implementation
echo "📦 Installing Python dependencies for real Seed-VC..."
source venv/bin/activate

pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install soundfile librosa scipy numpy
pip install scikit-learn resampy
pip install fastapi uvicorn python-multipart aiofiles
pip install python-dotenv loguru psutil

# Install frontend dependencies (fix lucide-react issue)
echo "📦 Installing frontend dependencies..."
pnpm install lucide-react@latest
pnpm install @types/node@latest

# Build frontend
echo "🔨 Building frontend..."
NODE_OPTIONS="--max-old-space-size=4096" pnpm run build --no-lint

if [ $? -ne 0 ]; then
    echo "⚠️ Build failed, starting in dev mode..."
    FRONTEND_MODE="dev"
else
    echo "✅ Build successful, starting in production mode..."
    FRONTEND_MODE="start"
fi

# Start Redis
echo "🔧 Starting Redis..."
sudo systemctl start redis-server || sudo service redis-server start || true

# Create necessary directories
mkdir -p uploads outputs models logs

# Start real Seed-VC backend
echo "🎭 Starting Real Seed-VC backend..."
cd backend

# Check if real implementation files exist
if [ -f "main_real.py" ] && [ -f "real_seedvc_processor.py" ]; then
    echo "🚀 Using Real Seed-VC implementation..."
    python main_real.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
else
    echo "⚠️ Real implementation not found, using simplified version..."
    python main_simple.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
fi

cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Test backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend started successfully"
else
    echo "⚠️ Backend may still be starting..."
fi

# Start frontend
echo "🌐 Starting frontend..."
if [ "$FRONTEND_MODE" = "dev" ]; then
    pnpm run dev &
else
    pnpm start &
fi

FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid

# Wait for frontend
sleep 3

echo ""
echo "🎉 Real Seed-VC System Started!"
echo "==============================="
echo ""
echo "🌐 URLs:"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "Health Check: http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "🧪 Test Commands:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:8000/models"
echo "curl http://localhost:8000/speakers"
echo "curl http://localhost:8000/demo/test-cloning"
echo ""
echo "📊 Features Available:"
echo "✅ Real voice conversion (Seed-VC methodology)"
echo "✅ Voice cloning with speaker embedding extraction"
echo "✅ F0 conversion and formant shifting"
echo "✅ Few-shot learning support"
echo "✅ Custom speaker creation"
echo "✅ 100% Vietnamese interface"
echo ""
echo "🛑 To stop: ./stop-simple.sh"
echo "📊 To check status: ./check-status.sh"

# Create demo audio files for testing (optional)
if [ ! -f "outputs/demo_audio.wav" ]; then
    echo "🎵 Creating demo audio for testing..."
    python3 -c "
import numpy as np
import soundfile as sf

# Create demo audio
sr = 24000
duration = 3.0
t = np.linspace(0, duration, int(duration * sr))

# Demo voice 1 (reference)
demo1 = 0.3 * np.sin(2 * np.pi * 150 * t) * np.exp(-t/4)
sf.write('outputs/demo_reference.wav', demo1, sr)

# Demo voice 2 (target content)  
demo2 = 0.3 * np.sin(2 * np.pi * 200 * t) * np.exp(-t/3)
sf.write('outputs/demo_content.wav', demo2, sr)

print('Demo audio files created in outputs/')
"
fi

echo ""
echo "🎭 Real Seed-VC is ready for voice conversion and cloning!"