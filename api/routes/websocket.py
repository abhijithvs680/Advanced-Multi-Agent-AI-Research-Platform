"""
WebSocket API for real-time updates.
Provides live job status, agent progress, and metrics streaming.
"""
import asyncio
import json
from typing import Dict, Set, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager

from shared.database import get_db_manager
from shared.models import Job

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from shared.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class EventType(str, Enum):
    """WebSocket event types"""
    JOB_STATUS = "job_status"
    AGENT_PROGRESS = "agent_progress"
    METRICS_UPDATE = "metrics_update"
    SYSTEM_STATUS = "system_status"
    LOG_MESSAGE = "log_message"


@dataclass
class WSEvent:
    """WebSocket event structure"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: str = None
    job_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "job_id": self.job_id
        })


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        # All active connections
        self.active_connections: Set[WebSocket] = set()
        
        # Connections subscribed to specific jobs
        self.job_subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # Background broadcast task
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("ws_connected", connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        """Remove a connection"""
        self.active_connections.discard(websocket)
        
        # Remove from job subscriptions
        for job_id in list(self.job_subscriptions.keys()):
            self.job_subscriptions[job_id].discard(websocket)
            if not self.job_subscriptions[job_id]:
                del self.job_subscriptions[job_id]
        
        logger.info("ws_disconnected", connections=len(self.active_connections))
    
    def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe a connection to job-specific updates"""
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = set()
        self.job_subscriptions[job_id].add(websocket)
        logger.info("ws_subscribed", job_id=job_id)
    
    def unsubscribe_from_job(self, websocket: WebSocket, job_id: str):
        """Unsubscribe from job updates"""
        if job_id in self.job_subscriptions:
            self.job_subscriptions[job_id].discard(websocket)
    
    async def send_personal(self, websocket: WebSocket, event: WSEvent):
        """Send event to a specific connection"""
        try:
            if websocket.application_state == WebSocketState.CONNECTED:
                await websocket.send_text(event.to_json())
        except Exception as e:
            logger.error("ws_send_failed", error=str(e))
            self.disconnect(websocket)
    
    async def broadcast(self, event: WSEvent):
        """Broadcast event to all connections"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                if connection.application_state == WebSocketState.CONNECTED:
                    await connection.send_text(event.to_json())
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_job(self, job_id: str, event: WSEvent):
        """Broadcast event to connections subscribed to a job"""
        event.job_id = job_id
        
        subscribers = self.job_subscriptions.get(job_id, set())
        disconnected = set()
        
        for connection in subscribers:
            try:
                if connection.application_state == WebSocketState.CONNECTED:
                    await connection.send_text(event.to_json())
            except Exception:
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


# Global connection manager
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager"""
    return manager


# ==================== Event Emitters ====================

async def emit_job_status(
    job_id: str,
    status: str,
    current_state: Optional[str] = None,
    progress: Optional[float] = None,
    message: Optional[str] = None
):
    """Emit job status update"""
    event = WSEvent(
        event_type=EventType.JOB_STATUS,
        job_id=job_id,
        data={
            "status": status,
            "current_state": current_state,
            "progress": progress,
            "message": message
        }
    )
    await manager.broadcast_to_job(job_id, event)
    await manager.broadcast(event)  # Also broadcast to all


async def emit_agent_progress(
    job_id: str,
    agent_name: str,
    step: str,
    progress: float,
    details: Optional[Dict[str, Any]] = None
):
    """Emit agent progress update"""
    event = WSEvent(
        event_type=EventType.AGENT_PROGRESS,
        job_id=job_id,
        data={
            "agent_name": agent_name,
            "step": step,
            "progress": progress,
            "details": details or {}
        }
    )
    await manager.broadcast_to_job(job_id, event)


async def emit_metrics_update(metrics: Dict[str, Any]):
    """Emit system metrics update"""
    event = WSEvent(
        event_type=EventType.METRICS_UPDATE,
        data=metrics
    )
    await manager.broadcast(event)


async def emit_log_message(
    job_id: str,
    level: str,
    message: str,
    agent_name: Optional[str] = None
):
    """Emit log message"""
    event = WSEvent(
        event_type=EventType.LOG_MESSAGE,
        job_id=job_id,
        data={
            "level": level,
            "message": message,
            "agent_name": agent_name
        }
    )
    await manager.broadcast_to_job(job_id, event)


async def send_initial_job_state(websocket: WebSocket, job_id: str):
    """Send current job state to a single connection upon subscription"""
    try:
        db_manager = get_db_manager()
        with db_manager.get_session() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                event = WSEvent(
                    event_type=EventType.JOB_STATUS,
                    job_id=job_id,
                    data={
                        "status": job.status.value,
                        "current_state": job.current_state.value if job.current_state else None,
                        "progress": job.progress,
                        "message": job.message
                    }
                )
                await manager.send_personal(websocket, event)
    except Exception as e:
        logger.error("ws_send_initial_state_failed", job_id=job_id, error=str(e))


# ==================== WebSocket Endpoints ====================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    job_id = message.get("job_id")
                    if job_id:
                        manager.subscribe_to_job(websocket, job_id)
                        await manager.send_personal(websocket, WSEvent(
                            event_type=EventType.SYSTEM_STATUS,
                            data={"message": f"Subscribed to job {job_id}"}
                        ))
                        # Send current state immediately
                        await send_initial_job_state(websocket, job_id)
                
                elif action == "unsubscribe":
                    job_id = message.get("job_id")
                    if job_id:
                        manager.unsubscribe_from_job(websocket, job_id)
                
                elif action == "ping":
                    await manager.send_personal(websocket, WSEvent(
                        event_type=EventType.SYSTEM_STATUS,
                        data={"message": "pong"}
                    ))
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/job/{job_id}")
async def job_websocket_endpoint(websocket: WebSocket, job_id: str):
    """Job-specific WebSocket endpoint"""
    await manager.connect(websocket)
    manager.subscribe_to_job(websocket, job_id)
    
    # Send initial subscription confirmation
    await manager.send_personal(websocket, WSEvent(
        event_type=EventType.SYSTEM_STATUS,
        data={"message": f"Connected to job {job_id}", "job_id": job_id}
    ))
    # Send current state immediately
    await send_initial_job_state(websocket, job_id)
    
    try:
        while True:
            # Keep connection alive, handle pings
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    await manager.send_personal(websocket, WSEvent(
                        event_type=EventType.SYSTEM_STATUS,
                        data={"message": "pong"}
                    ))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
