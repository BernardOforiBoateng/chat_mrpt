"""
Redis-based State Manager for Multi-Worker Environments
Provides a single source of truth for all workflow state across workers.
"""

import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class AnalysisStatus(Enum):
    """Analysis workflow statuses"""
    NOT_STARTED = "not_started"
    DATA_UPLOADED = "data_uploaded"
    TPR_COMPLETE = "tpr_complete"
    RISK_ANALYZING = "risk_analyzing"
    RISK_COMPLETE = "risk_complete"
    ITN_PLANNING = "itn_planning"
    ITN_COMPLETE = "itn_complete"
    REPORT_GENERATING = "report_generating"
    COMPLETE = "complete"


@dataclass
class WorkflowState:
    """Workflow state data structure"""
    session_id: str
    status: str
    data_loaded: bool = False
    csv_loaded: bool = False
    shapefile_loaded: bool = False
    tpr_completed: bool = False
    analysis_complete: bool = False
    itn_planning_complete: bool = False
    last_updated: str = None
    worker_id: str = None
    checksum: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


class RedisStateManager:
    """
    Manages workflow state in Redis for multi-worker consistency.
    This is THE authoritative source for all state across workers.
    """
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection."""
        self.redis_client = None
        self._connect(redis_url)
        self.ttl = 86400  # 24 hours default TTL
        
    def _connect(self, redis_url: str = None):
        """Connect to Redis."""
        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # Try to get from environment or config
                import os
                redis_host = os.environ.get('REDIS_HOST', 'localhost')
                redis_port = int(os.environ.get('REDIS_PORT', 6379))
                redis_db = int(os.environ.get('REDIS_DB', 0))
                
                # For production, try ElastiCache endpoint
                if 'production' in os.environ.get('FLASK_ENV', '').lower():
                    redis_host = 'chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com'
                
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            # Fallback to in-memory storage (not ideal but prevents crashes)
            self.redis_client = None
            self._fallback_storage = {}
    
    def _get_state_key(self, session_id: str) -> str:
        """Generate Redis key for session state."""
        return f"chatmrpt:state:{session_id}"
    
    def _get_lock_key(self, session_id: str) -> str:
        """Generate Redis key for distributed lock."""
        return f"chatmrpt:lock:{session_id}"
    
    def get_state(self, session_id: str) -> Optional[WorkflowState]:
        """
        Get current state for a session.
        This is called by EVERY worker to check state.
        """
        try:
            if not self.redis_client:
                # Fallback mode
                return self._fallback_storage.get(session_id)
            
            key = self._get_state_key(session_id)
            data = self.redis_client.get(key)
            
            if data:
                state_dict = json.loads(data)
                return WorkflowState(**state_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting state for {session_id}: {e}")
            return None
    
    def set_state(self, state: WorkflowState, worker_id: str = None) -> bool:
        """
        Set state for a session with atomic operation.
        This ensures only one worker can update at a time.
        """
        try:
            if not self.redis_client:
                # Fallback mode
                self._fallback_storage[state.session_id] = state
                return True
            
            # Add worker ID and timestamp
            state.worker_id = worker_id or self._get_worker_id()
            state.last_updated = datetime.now().isoformat()
            
            # Calculate checksum for integrity
            state_dict = asdict(state)
            state.checksum = self._calculate_checksum(state_dict)
            
            # Atomic set with expiry
            key = self._get_state_key(state.session_id)
            value = json.dumps(asdict(state))
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.set(key, value, ex=self.ttl)
            pipe.publish(f"chatmrpt:updates:{state.session_id}", value)  # Notify other workers
            pipe.execute()
            
            logger.info(f"✅ State updated for {state.session_id} by worker {state.worker_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting state for {state.session_id}: {e}")
            return False
    
    def update_state(self, session_id: str, updates: Dict[str, Any], worker_id: str = None) -> bool:
        """
        Update specific fields in state atomically.
        This prevents race conditions between workers.
        """
        lock_key = self._get_lock_key(session_id)
        
        try:
            if not self.redis_client:
                # Fallback mode
                if session_id in self._fallback_storage:
                    state = self._fallback_storage[session_id]
                    for key, value in updates.items():
                        setattr(state, key, value)
                    return True
                return False
            
            # Distributed lock to prevent race conditions
            with self.redis_client.lock(lock_key, timeout=5):
                # Get current state
                current_state = self.get_state(session_id)
                
                if not current_state:
                    # Create new state
                    current_state = WorkflowState(
                        session_id=session_id,
                        status=AnalysisStatus.NOT_STARTED.value
                    )
                
                # Apply updates
                for key, value in updates.items():
                    if hasattr(current_state, key):
                        setattr(current_state, key, value)
                    else:
                        current_state.metadata[key] = value
                
                # Save updated state
                return self.set_state(current_state, worker_id)
                
        except redis.exceptions.LockError:
            logger.warning(f"Could not acquire lock for {session_id}, retrying...")
            # Retry logic could go here
            return False
        except Exception as e:
            logger.error(f"Error updating state for {session_id}: {e}")
            return False
    
    def mark_analysis_complete(self, session_id: str) -> bool:
        """
        Mark analysis as complete. This is THE authoritative way to mark completion.
        ALL workers will see this immediately.
        """
        logger.info(f"🎯 Marking analysis complete for {session_id}")
        
        updates = {
            'analysis_complete': True,
            'status': AnalysisStatus.RISK_COMPLETE.value,
            'analysis_completed_at': datetime.now().isoformat()
        }
        
        success = self.update_state(session_id, updates)
        
        if success:
            logger.info(f"✅ Analysis marked complete for {session_id} in Redis")
            # Also publish event for real-time updates
            if self.redis_client:
                self.redis_client.publish(
                    f"chatmrpt:events:{session_id}", 
                    json.dumps({'event': 'analysis_complete', 'timestamp': datetime.now().isoformat()})
                )
        else:
            logger.error(f"❌ Failed to mark analysis complete for {session_id}")
        
        return success
    
    def is_analysis_complete(self, session_id: str) -> bool:
        """
        Check if analysis is complete. This is called by EVERY worker.
        Returns the authoritative answer from Redis.
        """
        state = self.get_state(session_id)
        
        if state:
            complete = state.analysis_complete
            logger.debug(f"Analysis complete check for {session_id}: {complete} (from Redis)")
            return complete
        
        logger.debug(f"No state found for {session_id}, analysis not complete")
        return False
    
    def mark_itn_planning_complete(self, session_id: str) -> bool:
        """Mark ITN planning as complete."""
        updates = {
            'itn_planning_complete': True,
            'status': AnalysisStatus.ITN_COMPLETE.value,
            'itn_completed_at': datetime.now().isoformat()
        }
        return self.update_state(session_id, updates)
    
    def get_workflow_status(self, session_id: str) -> str:
        """Get current workflow status."""
        state = self.get_state(session_id)
        return state.status if state else AnalysisStatus.NOT_STARTED.value
    
    def _get_worker_id(self) -> str:
        """Get unique worker identifier."""
        import os
        import socket
        pid = os.getpid()
        hostname = socket.gethostname()
        return f"{hostname}:{pid}"
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Calculate checksum for state integrity."""
        # Remove checksum field before calculating
        data_copy = {k: v for k, v in data.items() if k != 'checksum'}
        data_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def clear_state(self, session_id: str) -> bool:
        """Clear state for a session (for testing or cleanup)."""
        try:
            if not self.redis_client:
                if session_id in self._fallback_storage:
                    del self._fallback_storage[session_id]
                return True
            
            key = self._get_state_key(session_id)
            self.redis_client.delete(key)
            logger.info(f"🧹 Cleared state for {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing state for {session_id}: {e}")
            return False
    
    def get_all_sessions(self) -> List[str]:
        """Get all active sessions (for monitoring)."""
        try:
            if not self.redis_client:
                return list(self._fallback_storage.keys())
            
            pattern = "chatmrpt:state:*"
            keys = self.redis_client.keys(pattern)
            # Extract session IDs from keys
            sessions = [key.replace("chatmrpt:state:", "") for key in keys]
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            return []
    
    def subscribe_to_updates(self, session_id: str):
        """
        Subscribe to state updates for a session.
        This allows workers to get real-time notifications.
        """
        if not self.redis_client:
            return None
        
        pubsub = self.redis_client.pubsub()
        channel = f"chatmrpt:updates:{session_id}"
        pubsub.subscribe(channel)
        return pubsub


# Global instance (singleton pattern)
_redis_state_manager = None

def get_redis_state_manager() -> RedisStateManager:
    """Get or create the global Redis state manager instance."""
    global _redis_state_manager
    if _redis_state_manager is None:
        _redis_state_manager = RedisStateManager()
    return _redis_state_manager