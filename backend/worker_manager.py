"""
Worker Manager Module
Manages multiple worker processes for concurrent audio processing
"""

import asyncio
import logging
import multiprocessing as mp
import os
import psutil
import signal
import time
from typing import Dict, List, Optional, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class WorkerStats:
    """Worker statistics"""
    worker_id: str
    pid: int
    status: str
    jobs_processed: int
    cpu_usage: float
    memory_usage: float
    last_activity: datetime
    uptime: float

class WorkerManager:
    """Manages worker processes for concurrent audio processing"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or self._calculate_optimal_workers()
        self.workers: Dict[str, Dict[str, Any]] = {}
        self.process_executor = None
        self.thread_executor = None
        self.worker_stats: Dict[str, WorkerStats] = {}
        self.is_running = False
        self.cleanup_task = None
        
    def _calculate_optimal_workers(self) -> int:
        """Calculate optimal number of workers based on system resources"""
        cpu_count = mp.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative approach for CPU-intensive tasks
        # Each worker needs ~2GB RAM for audio processing
        max_by_cpu = max(1, cpu_count - 1)  # Leave 1 CPU for system
        max_by_memory = max(1, int(memory_gb // 2))  # 2GB per worker
        
        optimal = min(max_by_cpu, max_by_memory, 8)  # Cap at 8 workers
        
        logger.info(f"Calculated optimal workers: {optimal} (CPU: {cpu_count}, RAM: {memory_gb:.1f}GB)")
        return optimal
    
    async def start(self):
        """Start worker manager"""
        if self.is_running:
            return
        
        logger.info(f"Starting worker manager with {self.max_workers} workers")
        
        # Create process pool for CPU-intensive tasks
        self.process_executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=mp.get_context('spawn')
        )
        
        # Create thread pool for I/O operations
        self.thread_executor = ThreadPoolExecutor(
            max_workers=self.max_workers * 2,
            thread_name_prefix="audio_io"
        )
        
        self.is_running = True
        
        # Start monitoring task
        self.cleanup_task = asyncio.create_task(self._monitor_workers())
        
        logger.info("Worker manager started successfully")
    
    async def stop(self):
        """Stop worker manager"""
        if not self.is_running:
            return
        
        logger.info("Stopping worker manager...")
        self.is_running = False
        
        # Cancel monitoring task
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Shutdown executors
        if self.process_executor:
            self.process_executor.shutdown(wait=True, cancel_futures=False)
        
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True, cancel_futures=False)
        
        logger.info("Worker manager stopped")
    
    async def submit_audio_task(self, task_func, *args, **kwargs) -> Any:
        """Submit CPU-intensive audio processing task"""
        if not self.is_running:
            raise RuntimeError("Worker manager not running")
        
        loop = asyncio.get_event_loop()
        
        try:
            # Submit to process pool for CPU-intensive work
            future = self.process_executor.submit(task_func, *args, **kwargs)
            result = await loop.run_in_executor(None, future.result)
            return result
            
        except Exception as e:
            logger.error(f"Error executing audio task: {e}")
            raise
    
    async def submit_io_task(self, task_func, *args, **kwargs) -> Any:
        """Submit I/O task to thread pool"""
        if not self.is_running:
            raise RuntimeError("Worker manager not running")
        
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                self.thread_executor, 
                task_func, 
                *args, 
                **kwargs
            )
            return result
            
        except Exception as e:
            logger.error(f"Error executing I/O task: {e}")
            raise
    
    async def _monitor_workers(self):
        """Monitor worker health and performance"""
        while self.is_running:
            try:
                await self._update_worker_stats()
                await self._cleanup_completed_jobs()
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _update_worker_stats(self):
        """Update worker statistics"""
        try:
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Update global stats
            self.worker_stats["system"] = WorkerStats(
                worker_id="system",
                pid=os.getpid(),
                status="monitoring",
                jobs_processed=0,
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                last_activity=datetime.now(),
                uptime=time.time() - psutil.Process().create_time()
            )
            
        except Exception as e:
            logger.error(f"Error updating worker stats: {e}")
    
    async def _cleanup_completed_jobs(self):
        """Cleanup old completed jobs"""
        try:
            from redis_manager import redis_manager
            
            # Get completed jobs older than 1 hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            job_keys = await redis_manager.async_redis.keys("job:*")
            
            for job_key in job_keys:
                job_data = await redis_manager.async_redis.hgetall(job_key)
                
                if job_data.get("status") in ["completed", "failed", "cancelled"]:
                    completed_at = job_data.get("completed_at")
                    
                    if completed_at:
                        try:
                            completed_time = datetime.fromisoformat(completed_at)
                            
                            if completed_time < cutoff_time:
                                await redis_manager.async_redis.delete(job_key)
                                logger.info(f"Cleaned up old job: {job_key}")
                                
                        except Exception:
                            continue
            
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}")
    
    def get_worker_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get current worker statistics"""
        stats = {}
        
        for worker_id, worker_stat in self.worker_stats.items():
            stats[worker_id] = {
                "worker_id": worker_stat.worker_id,
                "pid": worker_stat.pid,
                "status": worker_stat.status,
                "jobs_processed": worker_stat.jobs_processed,
                "cpu_usage": worker_stat.cpu_usage,
                "memory_usage": worker_stat.memory_usage,
                "uptime": worker_stat.uptime
            }
        
        return stats
    
    async def scale_workers(self, new_worker_count: int):
        """Dynamically scale number of workers"""
        if new_worker_count == self.max_workers:
            return
        
        if new_worker_count < 1 or new_worker_count > 16:
            raise ValueError("Worker count must be between 1 and 16")
        
        logger.info(f"Scaling workers from {self.max_workers} to {new_worker_count}")
        
        # Stop current workers
        await self.stop()
        
        # Update worker count
        self.max_workers = new_worker_count
        
        # Restart with new worker count
        await self.start()
    
    async def get_queue_info(self) -> Dict[str, Any]:
        """Get detailed queue information"""
        try:
            from redis_manager import redis_manager
            
            # Queue size
            queue_size = await redis_manager.async_redis.zcard("job_queue")
            
            # Processing jobs
            job_keys = await redis_manager.async_redis.keys("job:*")
            processing_jobs = 0
            
            for job_key in job_keys:
                status = await redis_manager.async_redis.hget(job_key, "status")
                if status == "processing":
                    processing_jobs += 1
            
            # Estimate wait time
            avg_processing_time = 120  # 2 minutes average
            estimated_wait = (queue_size / self.max_workers) * avg_processing_time
            
            return {
                "queue_size": queue_size,
                "processing_jobs": processing_jobs,
                "max_workers": self.max_workers,
                "estimated_wait_time": estimated_wait,
                "worker_utilization": (processing_jobs / self.max_workers) * 100 if self.max_workers > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {}

# Global worker manager instance
worker_manager = WorkerManager()

# Utility functions for worker processes
def process_audio_file(input_path: str, output_path: str, processing_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process audio file in separate process
    This function runs in a separate process for CPU isolation
    """
    try:
        import numpy as np
        import soundfile as sf
        import librosa
        
        # Load audio
        audio, sr = sf.read(input_path)
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio)
        
        # Resample if needed
        target_sr = processing_params.get("sample_rate", 22050)
        if sr != target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        
        # Apply processing based on type
        processing_type = processing_params.get("type", "conversion")
        
        if processing_type == "conversion":
            # Voice conversion processing
            processed_audio = _process_voice_conversion(audio, processing_params)
        elif processing_type == "cloning":
            # Voice cloning processing
            reference_path = processing_params.get("reference_path")
            if reference_path:
                ref_audio, ref_sr = sf.read(reference_path)
                if len(ref_audio.shape) > 1:
                    ref_audio = librosa.to_mono(ref_audio)
                if ref_sr != target_sr:
                    ref_audio = librosa.resample(ref_audio, orig_sr=ref_sr, target_sr=target_sr)
                processed_audio = _process_voice_cloning(audio, ref_audio, processing_params)
            else:
                processed_audio = audio
        else:
            processed_audio = audio
        
        # Save result
        sf.write(output_path, processed_audio, target_sr)
        
        return {
            "success": True,
            "output_path": output_path,
            "duration": len(processed_audio) / target_sr,
            "sample_rate": target_sr,
            "channels": 1 if len(processed_audio.shape) == 1 else processed_audio.shape[1]
        }
        
    except Exception as e:
        logger.error(f"Error processing audio file: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def _process_voice_conversion(audio: "np.ndarray", params: Dict[str, Any]) -> "np.ndarray":
    """Process voice conversion (simplified for CPU)"""
    import numpy as np
    
    # Basic voice conversion simulation
    processed = audio.copy()
    
    # Apply gain based on target speaker
    gain = params.get("conversion_strength", 0.8)
    processed *= (1.0 + gain * 0.2)
    
    # Apply simple pitch shift
    pitch_factor = params.get("preserve_pitch", 0.5)
    if pitch_factor != 0.5:
        shift = (pitch_factor - 0.5) * 0.1
        processed = _apply_pitch_shift(processed, shift)
    
    # Normalize
    max_val = np.max(np.abs(processed))
    if max_val > 0.95:
        processed = processed * 0.95 / max_val
    
    return processed

def _process_voice_cloning(target_audio: "np.ndarray", reference_audio: "np.ndarray", params: Dict[str, Any]) -> "np.ndarray":
    """Process voice cloning (simplified for CPU)"""
    import numpy as np
    
    # Basic voice cloning simulation
    similarity = params.get("similarity_threshold", 0.8)
    
    # Match energy levels
    ref_energy = np.sqrt(np.mean(reference_audio**2))
    target_energy = np.sqrt(np.mean(target_audio**2))
    
    if target_energy > 0:
        energy_ratio = ref_energy / target_energy
        cloned_audio = target_audio * (energy_ratio * similarity + 1.0 * (1 - similarity))
    else:
        cloned_audio = target_audio
    
    # Apply spectral matching (simplified)
    cloned_audio = _match_spectral_characteristics(cloned_audio, reference_audio, similarity)
    
    # Normalize
    max_val = np.max(np.abs(cloned_audio))
    if max_val > 0.95:
        cloned_audio = cloned_audio * 0.95 / max_val
    
    return cloned_audio

def _apply_pitch_shift(audio: "np.ndarray", shift_factor: float) -> "np.ndarray":
    """Apply simple pitch shift"""
    import numpy as np
    
    if abs(shift_factor) < 0.01:
        return audio
    
    # Simple time-domain pitch shift
    new_length = int(len(audio) * (1 + shift_factor))
    indices = np.linspace(0, len(audio) - 1, new_length)
    shifted = np.interp(indices, np.arange(len(audio)), audio)
    
    # Crop or pad to original length
    if len(shifted) > len(audio):
        return shifted[:len(audio)]
    else:
        padded = np.zeros_like(audio)
        padded[:len(shifted)] = shifted
        return padded

def _match_spectral_characteristics(target: "np.ndarray", reference: "np.ndarray", strength: float) -> "np.ndarray":
    """Match spectral characteristics between audio signals"""
    import numpy as np
    
    # Simple frequency domain matching
    target_fft = np.fft.fft(target)
    ref_fft = np.fft.fft(reference[:len(target)])
    
    # Match magnitude spectrum
    target_mag = np.abs(target_fft)
    ref_mag = np.abs(ref_fft)
    target_phase = np.angle(target_fft)
    
    # Blend magnitudes
    blended_mag = ref_mag * strength + target_mag * (1 - strength)
    
    # Reconstruct signal
    blended_fft = blended_mag * np.exp(1j * target_phase)
    result = np.real(np.fft.ifft(blended_fft))
    
    return result.astype(np.float32)