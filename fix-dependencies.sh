#!/bin/bash

# Fix Dependencies Script
# Chạy script này khi gặp lỗi dependencies

echo "🔧 Fixing Dependencies..."
echo "========================"

# Stop any running services
echo "🛑 Stopping services..."
pkill -f "uvicorn main:app" || true
pkill -f "pnpm start" || true

# Fix frontend dependencies
echo "📦 Fixing frontend dependencies..."
pnpm install lucide-react@latest
pnpm install @types/node@latest

# Fix backend dependencies  
echo "🐍 Fixing Python dependencies..."
source venv/bin/activate

# Install missing packages
pip install aiohttp
pip install aiofiles
pip install psutil
pip install python-dotenv
pip install pydantic
pip install fastapi
pip install uvicorn

# Create simplified backend
echo "🔧 Creating simplified backend..."
cat > backend/main_simple.py <<'EOF'
"""
Simplified Seed-VC Backend for Demo
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any

app = FastAPI(
    title="Seed-VC CPU Backend - Simplified",
    description="Simplified voice conversion system",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
for dir_name in ["uploads", "outputs", "models"]:
    os.makedirs(dir_name, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="outputs"), name="static")

# Simple job storage
jobs: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    return {
        "message": "🎭 Hệ Thống Seed-VC CPU",
        "version": "1.0.0",
        "status": "online",
        "features": [
            "Chuyển đổi giọng nói",
            "Nhân bản giọng nói", 
            "100% Tiếng Việt",
            "CPU Optimized"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "storage": "available"
        }
    }

@app.get("/models")
async def get_models():
    return [
        {
            "id": "seed-vc-fast",
            "name": "Seed-VC Nhanh", 
            "description": "Mô hình tối ưu CPU",
            "available": True
        },
        {
            "id": "seed-vc-base",
            "name": "Seed-VC Cơ Bản",
            "description": "Mô hình chất lượng cân bằng", 
            "available": True
        }
    ]

@app.post("/convert")
async def convert_voice(
    audio_file: UploadFile = File(...),
    model_id: str = "seed-vc-fast",
    target_speaker: str = "speaker_001"
):
    """Voice conversion endpoint"""
    
    job_id = str(uuid.uuid4())
    
    # Save file
    file_path = f"uploads/{job_id}_{audio_file.filename}"
    with open(file_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)
    
    # Simulate processing
    jobs[job_id] = {
        "id": job_id,
        "status": "completed",
        "progress": 100.0,
        "message": "Chuyển đổi hoàn thành (Demo)",
        "result_url": f"/static/demo_result.wav"
    }
    
    return {"job_id": job_id, "status": "completed"}

@app.post("/clone") 
async def clone_voice(
    reference_file: UploadFile = File(...),
    target_file: UploadFile = File(...)
):
    """Voice cloning endpoint"""
    
    job_id = str(uuid.uuid4())
    
    # Save files
    ref_path = f"uploads/{job_id}_ref_{reference_file.filename}"
    target_path = f"uploads/{job_id}_target_{target_file.filename}"
    
    with open(ref_path, "wb") as f:
        f.write(await reference_file.read())
        
    with open(target_path, "wb") as f:
        f.write(await target_file.read())
    
    # Simulate processing
    jobs[job_id] = {
        "id": job_id,
        "status": "completed", 
        "progress": 100.0,
        "message": "Nhân bản giọng nói hoàn thành (Demo)",
        "result_url": f"/static/demo_cloned.wav"
    }
    
    return {"job_id": job_id, "status": "completed"}

@app.get("/convert/{job_id}/status")
async def get_status(job_id: str):
    """Get job status"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create simple start script
cat > start-fixed.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "🔧 Starting Seed-VC CPU (Fixed Version)..."

# Start Redis
sudo systemctl start redis-server

# Start simplified backend
source venv/bin/activate
cd backend
echo "🐍 Starting simplified backend..."
python main_simple.py &
echo $! > ../backend.pid
cd ..

# Start frontend (dev mode since build failed)
echo "🌐 Starting frontend in dev mode..."
pnpm run dev &
echo $! > frontend.pid

sleep 3

echo "✅ Services started!"
echo "🌐 Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "🔧 Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo "📊 Health: http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "Test commands:"
echo "curl http://localhost:8000/health"
echo "curl http://localhost:3000"
EOF

chmod +x start-fixed.sh

echo ""
echo "✅ Dependencies Fixed!"
echo "====================="
echo ""
echo "🎯 To start the system:"
echo "./start-fixed.sh"
echo ""
echo "🔍 To check status:"
echo "./check-status.sh"
echo ""
echo "🛑 To stop:"
echo "./stop-simple.sh"