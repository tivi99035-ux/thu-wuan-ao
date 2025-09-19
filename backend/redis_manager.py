"""
Redis Manager Module
Handles Redis connections, caching, and distributed task management
"""

import redis
import json
import pickle
import logging
import asyncio
from typing import Optional, Dict, Any, List
import aioredis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisManager:
    """Manages Redis connections and operations for distributed processing"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.async_redis = None
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize Redis connections"""
        try:
            # Async Redis connection for real-time operations
            self.async_redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            
            # Sync Redis connection for background tasks
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True
            )
            
            # Test connections
            await self.async_redis.ping()
            self.redis_client.ping()
            
            logger.info("Redis connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup Redis connections"""
        try:
            if self.async_redis:
                await self.async_redis.close()
            if self.connection_pool:
                self.connection_pool.disconnect()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
    
    # Job Management
    async def add_job(self, job_id: str, job_data: Dict[str, Any], priority: int = 1):
        """Add job to processing queue with priority"""
        try:
            # Store job data
            await self.async_redis.hset(f"job:{job_id}", mapping={
                "id": job_id,
                "data": json.dumps(job_data),
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "priority": priority,
                "attempts": 0
            })
            
            # Add to priority queue
            await self.async_redis.zadd("job_queue", {job_id: priority})
            
            # Set TTL for job data (24 hours)
            await self.async_redis.expire(f"job:{job_id}", 86400)
            
            logger.info(f"Job {job_id} added to queue with priority {priority}")
            
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {e}")
            raise
    
    async def get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job from priority queue"""
        try:
            # Get highest priority job (lowest score)
            result = await self.async_redis.zpopmin("job_queue", 1)
            
            if not result:
                return None
            
            job_id, priority = result[0]
            
            # Get job data
            job_data = await self.async_redis.hgetall(f"job:{job_id}")
            
            if not job_data:
                return None
            
            # Mark as processing
            await self.async_redis.hset(f"job:{job_id}", "status", "processing")
            await self.async_redis.hset(f"job:{job_id}", "started_at", datetime.now().isoformat())
            
            return {
                "id": job_id,
                "priority": int(priority),
                **job_data
            }
            
        except Exception as e:
            logger.error(f"Error getting next job: {e}")
            return None
    
    async def update_job_status(self, job_id: str, status: str, progress: float = None, message: str = None):
        """Update job status and progress"""
        try:
            updates = {"status": status}
            
            if progress is not None:
                updates["progress"] = str(progress)
            
            if message:
                updates["message"] = message
            
            if status in ["completed", "failed", "cancelled"]:
                updates["completed_at"] = datetime.now().isoformat()
            
            await self.async_redis.hset(f"job:{job_id}", mapping=updates)
            
            # Publish status update for real-time notifications
            await self.async_redis.publish(
                f"job_status:{job_id}",
                json.dumps({
                    "job_id": job_id,
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
            )
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        try:
            job_data = await self.async_redis.hgetall(f"job:{job_id}")
            
            if not job_data:
                return None
            
            # Parse JSON data if exists
            if "data" in job_data:
                try:
                    job_data["data"] = json.loads(job_data["data"])
                except:
                    pass
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return None
    
    # Session Management
    async def create_session(self, session_id: str, user_data: Dict[str, Any]):
        """Create user session"""
        try:
            session_data = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "jobs": json.dumps([]),
                **user_data
            }
            
            await self.async_redis.hset(f"session:{session_id}", mapping=session_data)
            await self.async_redis.expire(f"session:{session_id}", 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            session_data = await self.async_redis.hgetall(f"session:{session_id}")
            
            if not session_data:
                return None
            
            # Update last activity
            await self.async_redis.hset(f"session:{session_id}", "last_activity", datetime.now().isoformat())
            await self.async_redis.expire(f"session:{session_id}", 3600)
            
            # Parse jobs list
            if "jobs" in session_data:
                try:
                    session_data["jobs"] = json.loads(session_data["jobs"])
                except:
                    session_data["jobs"] = []
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def add_job_to_session(self, session_id: str, job_id: str):
        """Add job ID to user session"""
        try:
            session_data = await self.get_session(session_id)
            
            if session_data:
                jobs = session_data.get("jobs", [])
                if job_id not in jobs:
                    jobs.append(job_id)
                    # Keep only last 10 jobs per session
                    jobs = jobs[-10:]
                    
                await self.async_redis.hset(f"session:{session_id}", "jobs", json.dumps(jobs))
            
        except Exception as e:
            logger.error(f"Error adding job to session {session_id}: {e}")
    
    # Caching
    async def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value with TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, (str, bytes, int, float)):
                value = pickle.dumps(value)
                
            await self.async_redis.setex(key, ttl, value)
            
        except Exception as e:
            logger.error(f"Error setting cache {key}: {e}")
    
    async def cache_get(self, key: str) -> Any:
        """Get cache value"""
        try:
            value = await self.async_redis.get(key)
            
            if value is None:
                return None
            
            # Try to parse as JSON first
            try:
                return json.loads(value)
            except:
                # Try pickle if JSON fails
                try:
                    return pickle.loads(value.encode() if isinstance(value, str) else value)
                except:
                    return value
                    
        except Exception as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None
    
    async def cache_delete(self, key: str):
        """Delete cache key"""
        try:
            await self.async_redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {e}")
    
    # Statistics
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            stats = {}
            
            # Queue statistics
            stats["queue_size"] = await self.async_redis.zcard("job_queue")
            
            # Job status counts
            job_keys = await self.async_redis.keys("job:*")
            status_counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0}
            
            for job_key in job_keys[:1000]:  # Limit to avoid performance issues
                status = await self.async_redis.hget(job_key, "status")
                if status in status_counts:
                    status_counts[status] += 1
            
            stats["job_status"] = status_counts
            
            # Active sessions
            session_keys = await self.async_redis.keys("session:*")
            stats["active_sessions"] = len(session_keys)
            
            # Memory usage
            memory_info = await self.async_redis.info("memory")
            stats["memory_usage"] = {
                "used_memory": memory_info.get("used_memory", 0),
                "used_memory_human": memory_info.get("used_memory_human", "0B"),
                "used_memory_peak": memory_info.get("used_memory_peak", 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    # Rate Limiting
    async def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        try:
            key = f"rate_limit:{identifier}"
            current = await self.async_redis.get(key)
            
            if current is None:
                await self.async_redis.setex(key, window, 1)
                return True
            
            current_count = int(current)
            
            if current_count >= limit:
                return False
            
            await self.async_redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            return True  # Allow on error
    
    # Distributed Lock
    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        try:
            lock_key = f"lock:{lock_name}"
            identifier = f"{datetime.now().timestamp()}"
            
            result = await self.async_redis.set(
                lock_key, 
                identifier, 
                nx=True, 
                ex=timeout
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_name}: {e}")
            return False
    
    async def release_lock(self, lock_name: str):
        """Release distributed lock"""
        try:
            lock_key = f"lock:{lock_name}"
            await self.async_redis.delete(lock_key)
        except Exception as e:
            logger.error(f"Error releasing lock {lock_name}: {e}")

# Global Redis manager instance
redis_manager = RedisManager()