"""
WebSocket Manager Module
Handles real-time communication between frontend and backend
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections by session ID
        self.active_connections: Dict[str, WebSocket] = {}
        # Job subscriptions: job_id -> set of session_ids
        self.job_subscriptions: Dict[str, Set[str]] = {}
        # Session jobs: session_id -> set of job_ids
        self.session_jobs: Dict[str, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str = None) -> str:
        """Accept WebSocket connection and return session ID"""
        await websocket.accept()
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.active_connections[session_id] = websocket
        self.session_jobs[session_id] = set()
        self.connection_metadata[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ip_address": websocket.client.host if websocket.client else "unknown"
        }
        
        logger.info(f"WebSocket connected: {session_id}")
        
        # Send welcome message
        await self.send_to_session(session_id, {
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return session_id
    
    def disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # Clean up job subscriptions
        if session_id in self.session_jobs:
            for job_id in self.session_jobs[session_id]:
                if job_id in self.job_subscriptions:
                    self.job_subscriptions[job_id].discard(session_id)
                    if not self.job_subscriptions[job_id]:
                        del self.job_subscriptions[job_id]
            del self.session_jobs[session_id]
        
        if session_id in self.connection_metadata:
            del self.connection_metadata[session_id]
        
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific session"""
        if session_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))
            
            # Update last activity
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["last_activity"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")
            self.disconnect(session_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], exclude_sessions: Set[str] = None):
        """Broadcast message to all connected sessions"""
        if exclude_sessions is None:
            exclude_sessions = set()
        
        disconnected_sessions = []
        
        for session_id in self.active_connections:
            if session_id not in exclude_sessions:
                success = await self.send_to_session(session_id, message)
                if not success:
                    disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
    
    async def subscribe_to_job(self, session_id: str, job_id: str):
        """Subscribe session to job updates"""
        if session_id not in self.active_connections:
            return False
        
        # Add to subscriptions
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        
        self.job_subscriptions[job_id].add(session_id)
        self.session_jobs[session_id].add(job_id)
        
        logger.info(f"Session {session_id} subscribed to job {job_id}")
        return True
    
    async def unsubscribe_from_job(self, session_id: str, job_id: str):
        """Unsubscribe session from job updates"""
        if job_id in self.job_subscriptions:
            self.job_subscriptions[job_id].discard(session_id)
            
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
        
        if session_id in self.session_jobs:
            self.session_jobs[session_id].discard(job_id)
    
    async def notify_job_update(self, job_id: str, update_data: Dict[str, Any]):
        """Notify all subscribers about job update"""
        if job_id not in self.job_subscriptions:
            return
        
        message = {
            "type": "job_update",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            **update_data
        }
        
        disconnected_sessions = []
        
        for session_id in self.job_subscriptions[job_id]:
            success = await self.send_to_session(session_id, message)
            if not success:
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            await self.unsubscribe_from_job(session_id, job_id)
    
    async def send_system_status(self, session_id: str = None):
        """Send system status update"""
        try:
            from worker_manager import worker_manager
            from redis_manager import redis_manager
            
            # Get system statistics
            worker_stats = worker_manager.get_worker_stats()
            queue_info = await worker_manager.get_queue_info()
            system_stats = await redis_manager.get_system_stats()
            
            status_message = {
                "type": "system_status",
                "timestamp": datetime.now().isoformat(),
                "workers": worker_stats,
                "queue": queue_info,
                "system": system_stats,
                "connections": {
                    "active": len(self.active_connections),
                    "total_jobs": len(self.job_subscriptions)
                }
            }
            
            if session_id:
                await self.send_to_session(session_id, status_message)
            else:
                await self.broadcast(status_message)
                
        except Exception as e:
            logger.error(f"Error sending system status: {e}")
    
    async def handle_client_message(self, session_id: str, message: Dict[str, Any]):
        """Handle incoming message from client"""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe_job":
                job_id = message.get("job_id")
                if job_id:
                    await self.subscribe_to_job(session_id, job_id)
                    await self.send_to_session(session_id, {
                        "type": "subscription_confirmed",
                        "job_id": job_id
                    })
            
            elif message_type == "unsubscribe_job":
                job_id = message.get("job_id")
                if job_id:
                    await self.unsubscribe_from_job(session_id, job_id)
            
            elif message_type == "get_system_status":
                await self.send_system_status(session_id)
            
            elif message_type == "ping":
                await self.send_to_session(session_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                logger.warning(f"Unknown message type from {session_id}: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling client message from {session_id}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.active_connections)
        total_subscriptions = sum(len(subs) for subs in self.job_subscriptions.values())
        
        # Calculate connection duration
        now = datetime.now()
        connection_durations = []
        
        for session_id, metadata in self.connection_metadata.items():
            try:
                connected_at = datetime.fromisoformat(metadata["connected_at"])
                duration = (now - connected_at).total_seconds()
                connection_durations.append(duration)
            except:
                continue
        
        avg_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        return {
            "total_connections": total_connections,
            "total_subscriptions": total_subscriptions,
            "average_connection_duration": avg_duration,
            "longest_connection": max(connection_durations, default=0),
            "active_jobs": len(self.job_subscriptions)
        }

# Global connection manager instance
connection_manager = ConnectionManager()

# Background task for system monitoring
async def system_monitor_task():
    """Background task to send periodic system updates"""
    while True:
        try:
            await connection_manager.send_system_status()
            await asyncio.sleep(30)  # Send updates every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in system monitor task: {e}")
            await asyncio.sleep(10)