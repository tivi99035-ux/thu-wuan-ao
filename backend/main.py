"""
Seed-VC CPU-Optimized Backend
FastAPI server for voice conversion processing
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os
import json
import uuid
import aiofiles
import logging
from datetime import datetime
import time

from voice_processor import VoiceProcessor
from model_manager import ModelManager
from audio_utils import AudioProcessor
from queue_manager import ProcessingQueue
from redis_manager import RedisManager, redis_manager
from worker_manager import WorkerManager, worker_manager
from websocket_manager import ConnectionManager, connection_manager, system_monitor_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Seed-VC CPU Backend - Multi-User",
    description="CPU-optimized voice conversion system with multi-user support",
    version="2.0.0"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
model_manager = ModelManager()
voice_processor = VoiceProcessor()
audio_processor = AudioProcessor()
processing_queue = ProcessingQueue()

# Directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
MODELS_DIR = "models"

for directory in [UPLOAD_DIR, OUTPUT_DIR, MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="outputs"), name="static")

# Pydantic models
class ConversionRequest(BaseModel):
    model_id: str
    target_speaker: str
    conversion_strength: float = 0.8
    preserve_pitch: float = 0.5
    noise_reduction: float = 0.3

class ConversionStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    result_url: Optional[str] = None
    error: Optional[str] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    language: str
    gender: str
    available: bool
    size_mb: float
    download_url: Optional[str] = None

# Import psutil for system monitoring
import psutil
from worker_manager import process_audio_file

# Jobs are now managed by Redis - keeping this for compatibility
jobs: Dict[str, Dict[str, Any]] = {}

# Rate limiting dependency
async def rate_limit_check(request):
    """Check rate limiting for requests"""
    client_ip = request.client.host
    
    # Check if Redis is available
    try:
        is_allowed = await redis_manager.check_rate_limit(
            identifier=f"api:{client_ip}",
            limit=30,  # 30 requests per minute
            window=60
        )
        
        if not is_allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
    except Exception as e:
        # Allow request if Redis is not available
        logger.warning(f"Rate limiting check failed: {e}")
        pass

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Seed-VC CPU Multi-User Backend...")
    
    try:
        # Initialize Redis manager
        await redis_manager.initialize()
        logger.info("Redis manager initialized")
        
        # Initialize worker manager
        await worker_manager.start()
        logger.info("Worker manager started")
        
        # Initialize model manager
        await model_manager.initialize()
        
        # Load available models
        await model_manager.load_default_models()
        
        # Start system monitoring task
        asyncio.create_task(system_monitor_task())
        
        logger.info("Multi-user backend initialization complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down multi-user backend...")
    
    try:
        # Cleanup managers
        await worker_manager.stop()
        await model_manager.cleanup()
        await redis_manager.cleanup()
        
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hệ Thống Seed-VC CPU - Đa Người Dùng",
        "version": "2.0.0",
        "status": "online",
        "features": [
            "Chuyển đổi giọng nói",
            "Nhân bản giọng nói AI", 
            "Xử lý đồng thời nhiều người dùng",
            "Tối ưu CPU"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Get detailed system health
        worker_stats = worker_manager.get_worker_stats()
        queue_info = await worker_manager.get_queue_info()
        redis_stats = await redis_manager.get_system_stats()
        connection_stats = connection_manager.get_connection_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "models_loaded": len(model_manager.loaded_models),
            "workers": {
                "active": worker_manager.max_workers,
                "stats": worker_stats
            },
            "queue": queue_info,
            "redis": redis_stats,
            "connections": connection_stats,
            "system": {
                "cpu_count": os.cpu_count(),
                "memory_total": f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
                "uptime": time.time() - psutil.Process().create_time()
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/models", response_model=list[ModelInfo])
async def get_models():
    """Get available voice conversion models"""
    try:
        models = await model_manager.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models")

@app.post("/models/{model_id}/download")
async def download_model(model_id: str, background_tasks: BackgroundTasks):
    """Download and install a voice conversion model"""
    try:
        # Add download task to background
        background_tasks.add_task(model_manager.download_model, model_id)
        
        return {
            "message": f"Model {model_id} download started",
            "status": "downloading"
        }
    except Exception as e:
        logger.error(f"Error starting model download: {e}")
        raise HTTPException(status_code=500, detail="Failed to start model download")

@app.post("/clone")
async def clone_voice(
    background_tasks: BackgroundTasks,
    reference_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
    similarity_threshold: float = 0.8,
    session_id: Optional[str] = None
):
    """Start voice cloning process with multi-user support"""
    
    # Rate limiting check for cloning (more restrictive)
    client_ip = "unknown"
    is_allowed = await redis_manager.check_rate_limit(
        identifier=f"clone:{client_ip}",
        limit=3,  # 3 cloning jobs per hour per IP
        window=3600
    )
    
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Đã vượt quá giới hạn nhân bản giọng nói. Vui lòng thử lại sau 1 giờ.")
    
    # Validate files
    for file in [reference_file, target_file]:
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Định dạng tệp âm thanh không hợp lệ")
        
        if file.size > 50 * 1024 * 1024:  # 50MB limit for cloning
            raise HTTPException(status_code=400, detail="Kích thước tệp quá lớn cho nhân bản giọng nói. Tối đa 50MB.")
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create user-specific directory
        user_dir = os.path.join(UPLOAD_DIR, session_id or "anonymous")
        os.makedirs(user_dir, exist_ok=True)
        
        # Save uploaded files
        ref_extension = reference_file.filename.split('.')[-1].lower()
        target_extension = target_file.filename.split('.')[-1].lower()
        
        ref_path = os.path.join(user_dir, f"{job_id}_ref.{ref_extension}")
        target_path = os.path.join(user_dir, f"{job_id}_target.{target_extension}")
        
        async with aiofiles.open(ref_path, 'wb') as f:
            ref_content = await reference_file.read()
            await f.write(ref_content)
            
        async with aiofiles.open(target_path, 'wb') as f:
            target_content = await target_file.read()
            await f.write(target_content)
        
        # Create job data
        job_data = {
            "type": "cloning",
            "reference_path": ref_path,
            "target_path": target_path,
            "similarity_threshold": similarity_threshold,
            "session_id": session_id,
            "client_ip": client_ip,
            "reference_filename": reference_file.filename,
            "target_filename": target_file.filename
        }
        
        # Add to Redis queue with higher priority for cloning
        priority = 0  # High priority for cloning
        await redis_manager.add_job(job_id, job_data, priority)
        
        # Add job to session if provided
        if session_id:
            await redis_manager.add_job_to_session(session_id, job_id)
        
        # Store in local jobs for compatibility
        jobs[job_id] = {
            "id": job_id,
            "type": "cloning",
            "status": "queued", 
            "progress": 0.0,
            "message": "Công việc nhân bản giọng nói đã được thêm vào hàng đợi",
            **job_data,
            "created_at": datetime.now().isoformat(),
            "result_url": None,
            "error": None
        }
        
        # Start processing
        background_tasks.add_task(process_voice_cloning, job_id)
        
        return {
            "job_id": job_id, 
            "status": "queued",
            "message": "Công việc nhân bản đã được thêm vào hàng đợi",
            "estimated_wait_time": (await worker_manager.get_queue_info()).get("estimated_wait_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Error starting voice cloning: {e}")
        raise HTTPException(status_code=500, detail="Không thể bắt đầu nhân bản giọng nói")

@app.post("/convert")
async def convert_voice(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    model_id: str = "seed-vc-fast",
    target_speaker: str = "speaker_001",
    conversion_strength: float = 0.8,
    preserve_pitch: float = 0.5,
    noise_reduction: float = 0.3,
    session_id: Optional[str] = None
):
    """Start voice conversion process with multi-user support"""
    
    # Rate limiting check
    client_ip = "unknown"  # In real implementation, get from request
    is_allowed = await redis_manager.check_rate_limit(
        identifier=f"convert:{client_ip}",
        limit=5,  # 5 conversions per minute per IP
        window=60
    )
    
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu. Vui lòng thử lại sau.")
    
    # Validate file
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Định dạng tệp âm thanh không hợp lệ")
    
    # Check file size (100MB limit)
    if audio_file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Kích thước tệp quá lớn. Tối đa 100MB.")
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file with user isolation
        file_extension = audio_file.filename.split('.')[-1].lower()
        user_dir = os.path.join(UPLOAD_DIR, session_id or "anonymous")
        os.makedirs(user_dir, exist_ok=True)
        
        input_path = os.path.join(user_dir, f"{job_id}.{file_extension}")
        
        async with aiofiles.open(input_path, 'wb') as f:
            content = await audio_file.read()
            await f.write(content)
        
        # Create job data
        job_data = {
            "type": "conversion",
            "input_path": input_path,
            "model_id": model_id,
            "target_speaker": target_speaker,
            "conversion_strength": conversion_strength,
            "preserve_pitch": preserve_pitch,
            "noise_reduction": noise_reduction,
            "session_id": session_id,
            "client_ip": client_ip,
            "filename": audio_file.filename
        }
        
        # Add to Redis queue with priority
        priority = 1  # Normal priority
        await redis_manager.add_job(job_id, job_data, priority)
        
        # Add job to session if provided
        if session_id:
            await redis_manager.add_job_to_session(session_id, job_id)
        
        # Store in local jobs for compatibility
        jobs[job_id] = {
            "id": job_id,
            "type": "conversion", 
            "status": "queued",
            "progress": 0.0,
            "message": "Công việc đã được thêm vào hàng đợi",
            **job_data,
            "created_at": datetime.now().isoformat(),
            "result_url": None,
            "error": None
        }
        
        # Start processing
        background_tasks.add_task(process_conversion, job_id)
        
        return {
            "job_id": job_id, 
            "status": "queued",
            "message": "Công việc đã được thêm vào hàng đợi xử lý",
            "estimated_wait_time": (await worker_manager.get_queue_info()).get("estimated_wait_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Error starting conversion: {e}")
        raise HTTPException(status_code=500, detail="Không thể bắt đầu chuyển đổi")

@app.get("/convert/{job_id}/status", response_model=ConversionStatus)
async def get_conversion_status(job_id: str):
    """Get conversion job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return ConversionStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result_url=job["result_url"],
        error=job["error"]
    )

@app.get("/convert/{job_id}/result")
async def get_conversion_result(job_id: str):
    """Download conversion result"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job["result_url"]:
        raise HTTPException(status_code=404, detail="Result file not found")
    
    # Return file stream
    output_path = job["result_url"].replace("/static/", "outputs/")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    
    def generate_file():
        with open(output_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate_file(),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=converted_{job_id}.wav"}
    )

@app.delete("/convert/{job_id}")
async def cancel_conversion(job_id: str):
    """Cancel a conversion job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")
    
    jobs[job_id]["status"] = "cancelled"
    jobs[job_id]["message"] = "Job cancelled by user"
    
    return {"message": "Job cancelled successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """WebSocket endpoint for real-time updates"""
    session_id = await connection_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await connection_manager.handle_client_message(session_id, message)
            except json.JSONDecodeError:
                await connection_manager.send_to_session(session_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        connection_manager.disconnect(session_id)

@app.get("/queue/status")
async def get_queue_status():
    """Get processing queue status"""
    try:
        queue_info = await worker_manager.get_queue_info()
        system_stats = await redis_manager.get_system_stats()
        
        return {
            **queue_info,
            "redis_stats": system_stats,
            "worker_stats": worker_manager.get_worker_stats(),
            "connections": connection_manager.get_connection_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {
            "queue_size": 0,
            "error": str(e)
        }

@app.get("/system/stats")
async def get_system_stats():
    """Get detailed system statistics"""
    try:
        return {
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
                },
                "cpu_count": os.cpu_count(),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            "workers": worker_manager.get_worker_stats(),
            "queue": await worker_manager.get_queue_info(),
            "connections": connection_manager.get_connection_stats(),
            "redis": await redis_manager.get_system_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system stats")

@app.post("/system/scale")
async def scale_workers(new_worker_count: int):
    """Scale the number of worker processes"""
    try:
        if new_worker_count < 1 or new_worker_count > 16:
            raise HTTPException(status_code=400, detail="Worker count must be between 1 and 16")
        
        await worker_manager.scale_workers(new_worker_count)
        
        return {
            "message": f"Scaled to {new_worker_count} workers",
            "new_worker_count": new_worker_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scaling workers: {e}")
        raise HTTPException(status_code=500, detail="Failed to scale workers")

async def process_voice_cloning(job_id: str):
    """Background task to process voice cloning with worker management"""
    try:
        job = jobs.get(job_id)
        if not job:
            # Try to get from Redis
            job_data = await redis_manager.get_job_status(job_id)
            if not job_data:
                logger.error(f"Job {job_id} not found")
                return
            job = job_data
        
        logger.info(f"Starting voice cloning for job {job_id}")
        
        # Update status in both local and Redis
        await update_job_status(job_id, "processing", 15.0, "Đang phân tích giọng nói tham khảo...")
        
        # Use worker manager for CPU-intensive processing
        from worker_manager import process_audio_file
        
        # Prepare processing parameters
        processing_params = {
            "type": "cloning",
            "reference_path": job["reference_path"],
            "similarity_threshold": job["similarity_threshold"],
            "sample_rate": 22050
        }
        
        # Update progress
        await update_job_status(job_id, "processing", 30.0, "Đang trích xuất đặc trưng giọng nói...")
        await asyncio.sleep(0.5)  # Allow status update to propagate
        
        await update_job_status(job_id, "processing", 50.0, "Đang tạo mô hình giọng nói...")
        await asyncio.sleep(0.5)
        
        await update_job_status(job_id, "processing", 70.0, "Đang áp dụng đặc trưng vào âm thanh đích...")
        
        # Process with worker manager
        session_id = job.get("session_id", "anonymous")
        output_dir = os.path.join(OUTPUT_DIR, session_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"cloned_{job_id}.wav")
        
        result = await worker_manager.submit_audio_task(
            process_audio_file,
            job["target_path"],
            output_path,
            processing_params
        )
        
        if result["success"]:
            await update_job_status(job_id, "completed", 100.0, "Nhân bản giọng nói hoàn thành thành công")
            
            # Update job with result
            if job_id in jobs:
                jobs[job_id]["result_url"] = f"/static/{session_id}/cloned_{job_id}.wav"
                jobs[job_id]["status"] = "completed"
            
            logger.info(f"Voice cloning completed for job {job_id}")
        else:
            await update_job_status(job_id, "failed", 0, f"Nhân bản giọng nói thất bại: {result['error']}")
            
    except Exception as e:
        logger.error(f"Voice cloning failed for job {job_id}: {e}")
        await update_job_status(job_id, "failed", 0, f"Nhân bản giọng nói thất bại: {str(e)}")

async def update_job_status(job_id: str, status: str, progress: float, message: str):
    """Update job status in both local storage and Redis, and notify via WebSocket"""
    try:
        # Update local storage
        if job_id in jobs:
            jobs[job_id]["status"] = status
            jobs[job_id]["progress"] = progress
            jobs[job_id]["message"] = message
            
            if status in ["completed", "failed", "cancelled"]:
                jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        # Update Redis
        await redis_manager.update_job_status(job_id, status, progress, message)
        
        # Notify via WebSocket
        await connection_manager.notify_job_update(job_id, {
            "status": status,
            "progress": progress,
            "message": message
        })
        
    except Exception as e:
        logger.error(f"Error updating job status for {job_id}: {e}")

async def process_conversion(job_id: str):
    """Background task to process voice conversion with worker management"""
    try:
        job = jobs.get(job_id)
        if not job:
            # Try to get from Redis
            job_data = await redis_manager.get_job_status(job_id)
            if not job_data:
                logger.error(f"Job {job_id} not found")
                return
            job = job_data
        
        logger.info(f"Starting conversion for job {job_id}")
        
        # Update status
        await update_job_status(job_id, "processing", 10.0, "Đang khởi tạo quy trình chuyển đổi...")
        
        # Load model if needed
        await model_manager.ensure_model_loaded(job["model_id"])
        await update_job_status(job_id, "processing", 25.0, "Mô hình giọng nói đã được tải")
        
        # Prepare processing parameters
        processing_params = {
            "type": "conversion",
            "model_id": job["model_id"],
            "target_speaker": job["target_speaker"],
            "conversion_strength": job["conversion_strength"],
            "preserve_pitch": job["preserve_pitch"],
            "noise_reduction": job["noise_reduction"],
            "sample_rate": 22050
        }
        
        await update_job_status(job_id, "processing", 40.0, "Đang tiền xử lý âm thanh...")
        await asyncio.sleep(0.5)
        
        await update_job_status(job_id, "processing", 55.0, "Đang trích xuất đặc trưng giọng nói...")
        await asyncio.sleep(0.5)
        
        await update_job_status(job_id, "processing", 70.0, "Đang chuyển đổi đặc điểm giọng nói...")
        
        # Process with worker manager
        session_id = job.get("session_id", "anonymous")
        output_dir = os.path.join(OUTPUT_DIR, session_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"converted_{job_id}.wav")
        
        result = await worker_manager.submit_audio_task(
            process_audio_file,
            job["input_path"],
            output_path,
            processing_params
        )
        
        if result["success"]:
            await update_job_status(job_id, "completed", 100.0, "Chuyển đổi hoàn thành thành công")
            
            # Update job with result
            if job_id in jobs:
                jobs[job_id]["result_url"] = f"/static/{session_id}/converted_{job_id}.wav"
                jobs[job_id]["status"] = "completed"
            
            logger.info(f"Conversion completed for job {job_id}")
        else:
            await update_job_status(job_id, "failed", 0, f"Chuyển đổi thất bại: {result['error']}")
            
    except Exception as e:
        logger.error(f"Conversion failed for job {job_id}: {e}")
        await update_job_status(job_id, "failed", 0, f"Chuyển đổi thất bại: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)