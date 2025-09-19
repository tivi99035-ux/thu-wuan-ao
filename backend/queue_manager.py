"""
Queue Manager Module
Handles processing queue for voice conversion jobs
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import heapq

logger = logging.getLogger(__name__)

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

class JobStatus(Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingJob:
    """Represents a voice conversion job"""
    id: str
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

class ProcessingQueue:
    """Manages the processing queue for voice conversion jobs"""
    
    def __init__(self, max_workers: int = 2, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self._queue: List[ProcessingJob] = []
        self._jobs: Dict[str, ProcessingJob] = {}
        self._workers: List[asyncio.Task] = []
        self._worker_semaphore = asyncio.Semaphore(max_workers)
        self._queue_lock = asyncio.Lock()
        self._running = False
        
    async def start(self):
        """Start the processing queue"""
        if self._running:
            return
            
        logger.info(f"Starting processing queue with {self.max_workers} workers")
        self._running = True
        
        # Start worker coroutines
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def stop(self):
        """Stop the processing queue"""
        if not self._running:
            return
            
        logger.info("Stopping processing queue")
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
    
    async def add_job(
        self,
        job_id: str,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingJob:
        """Add a job to the processing queue"""
        
        if len(self._queue) >= self.max_queue_size:
            raise RuntimeError("Processing queue is full")
        
        if job_id in self._jobs:
            raise ValueError(f"Job {job_id} already exists")
        
        async with self._queue_lock:
            job = ProcessingJob(
                id=job_id,
                priority=priority,
                status=JobStatus.QUEUED,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            
            self._jobs[job_id] = job
            heapq.heappush(self._queue, job)
            
            logger.info(f"Added job {job_id} to queue with priority {priority.name}")
            return job
    
    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get a job by ID"""
        return self._jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self._jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
        
        job.status = JobStatus.CANCELLED
        job.message = "Job cancelled by user"
        job.completed_at = datetime.now()
        
        logger.info(f"Cancelled job {job_id}")
        return True
    
    async def update_job_progress(
        self, 
        job_id: str, 
        progress: float, 
        message: str = ""
    ):
        """Update job progress"""
        job = self._jobs.get(job_id)
        if job:
            job.progress = progress
            if message:
                job.message = message
    
    async def complete_job(self, job_id: str, message: str = "Job completed"):
        """Mark job as completed"""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.message = message
            job.completed_at = datetime.now()
            logger.info(f"Completed job {job_id}")
    
    async def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.message = f"Job failed: {error}"
            job.completed_at = datetime.now()
            logger.error(f"Failed job {job_id}: {error}")
    
    def size(self) -> int:
        """Get current queue size"""
        return len(self._queue)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "queue_size": len(self._queue),
            "total_jobs": len(self._jobs),
            "max_workers": self.max_workers,
            "running": self._running,
            "status_counts": {}
        }
        
        # Count jobs by status
        for status in JobStatus:
            count = sum(1 for job in self._jobs.values() if job.status == status)
            stats["status_counts"][status.value] = count
        
        return stats
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes jobs"""
        logger.info(f"Worker {worker_name} started")
        
        while self._running:
            try:
                # Get next job from queue
                job = await self._get_next_job()
                if not job:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1.0)
                    continue
                
                # Acquire worker semaphore
                async with self._worker_semaphore:
                    await self._process_job(job, worker_name)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _get_next_job(self) -> Optional[ProcessingJob]:
        """Get the next job from the priority queue"""
        async with self._queue_lock:
            while self._queue:
                job = heapq.heappop(self._queue)
                
                # Skip cancelled jobs
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Mark job as processing
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                job.message = "Processing started"
                
                return job
        
        return None
    
    async def _process_job(self, job: ProcessingJob, worker_name: str):
        """Process a single job"""
        logger.info(f"Worker {worker_name} processing job {job.id}")
        
        try:
            # Import here to avoid circular imports
            from main import jobs, process_conversion
            
            # Check if job was cancelled
            if job.status == JobStatus.CANCELLED:
                return
            
            # Process the job
            await process_conversion(job.id)
            
        except Exception as e:
            logger.error(f"Job {job.id} processing failed: {e}")
            await self.fail_job(job.id, str(e))
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed/failed jobs"""
        current_time = datetime.now()
        jobs_to_remove = []
        
        for job_id, job in self._jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    age_hours = (current_time - job.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self._jobs[job_id]
            logger.info(f"Cleaned up old job {job_id}")
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    async def get_queue_status(self) -> List[Dict[str, Any]]:
        """Get status of all jobs in queue"""
        queue_status = []
        
        # Add queued jobs
        async with self._queue_lock:
            for job in sorted(self._queue, key=lambda x: (x.priority.value, x.created_at)):
                queue_status.append({
                    "id": job.id,
                    "status": job.status.value,
                    "priority": job.priority.name,
                    "progress": job.progress,
                    "message": job.message,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                })
        
        return queue_status
    
    async def estimate_wait_time(self, job_id: str) -> Optional[float]:
        """Estimate wait time for a job in seconds"""
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.QUEUED:
            return None
        
        # Count jobs ahead in queue with higher or equal priority
        jobs_ahead = 0
        async with self._queue_lock:
            for queued_job in self._queue:
                if queued_job.id == job_id:
                    break
                if queued_job.priority.value <= job.priority.value:
                    jobs_ahead += 1
        
        # Estimate processing time per job (in seconds)
        avg_processing_time = 60.0  # 1 minute average
        
        # Calculate wait time based on available workers
        estimated_wait = (jobs_ahead / self.max_workers) * avg_processing_time
        
        return estimated_wait