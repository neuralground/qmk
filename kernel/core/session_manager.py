"""
Session Manager for QMK Kernel

Manages tenant sessions, capability negotiation, and session-scoped resources.
"""

import secrets
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class SessionQuota:
    """Resource quotas for a session."""
    max_logical_qubits: int = 100
    max_channels: int = 10
    max_jobs: int = 5
    max_physical_qubits: int = 10000


@dataclass
class Session:
    """
    Represents an active tenant session.
    
    Tracks:
    - Session ID and tenant ID
    - Granted capabilities
    - Resource quotas
    - Active resources (jobs, qubits, channels)
    - Session creation time
    """
    session_id: str
    tenant_id: str
    granted_caps: Set[str]
    quota: SessionQuota
    created_at: float = field(default_factory=time.time)
    
    # Active resources
    active_jobs: Set[str] = field(default_factory=set)
    allocated_qubits: Set[str] = field(default_factory=set)
    open_channels: Set[str] = field(default_factory=set)
    
    def can_allocate_qubits(self, count: int) -> bool:
        """Check if session can allocate more qubits."""
        return len(self.allocated_qubits) + count <= self.quota.max_logical_qubits
    
    def can_create_job(self) -> bool:
        """Check if session can create more jobs."""
        return len(self.active_jobs) < self.quota.max_jobs
    
    def can_open_channel(self) -> bool:
        """Check if session can open more channels."""
        return len(self.open_channels) < self.quota.max_channels
    
    def has_capability(self, cap: str) -> bool:
        """Check if session has a specific capability."""
        return cap in self.granted_caps
    
    def has_capabilities(self, caps: List[str]) -> bool:
        """Check if session has all specified capabilities."""
        return all(cap in self.granted_caps for cap in caps)
    
    def missing_capabilities(self, required: List[str]) -> List[str]:
        """Get list of missing capabilities."""
        return [cap for cap in required if cap not in self.granted_caps]


class SessionManager:
    """
    Manages tenant sessions and capability negotiation.
    
    Responsibilities:
    - Session creation and lifecycle
    - Capability negotiation and validation
    - Resource quota enforcement
    - Session-scoped resource tracking
    """
    
    # Standard capabilities
    CAP_ALLOC = "CAP_ALLOC"          # Allocate logical qubits
    CAP_COMPUTE = "CAP_COMPUTE"      # Quantum gate operations
    CAP_MEASURE = "CAP_MEASURE"      # Measurement operations
    CAP_TELEPORT = "CAP_TELEPORT"    # Teleportation operations
    CAP_MAGIC = "CAP_MAGIC"          # Magic state distillation
    CAP_LINK = "CAP_LINK"            # Entanglement channels
    CAP_CHECKPOINT = "CAP_CHECKPOINT"  # Checkpoint/restore
    CAP_DEBUG = "CAP_DEBUG"          # Debug operations
    
    ALL_CAPABILITIES = {
        CAP_ALLOC, CAP_COMPUTE, CAP_MEASURE, CAP_TELEPORT, CAP_MAGIC, 
        CAP_LINK, CAP_CHECKPOINT, CAP_DEBUG
    }
    
    def __init__(self, default_quota: Optional[SessionQuota] = None):
        """
        Initialize session manager.
        
        Args:
            default_quota: Default quota for new sessions
        """
        self.default_quota = default_quota or SessionQuota()
        
        # Session tracking
        self.sessions: Dict[str, Session] = {}
        
        # Tenant -> session mapping (for multi-session support)
        self.tenant_sessions: Dict[str, Set[str]] = {}
    
    def negotiate_capabilities(
        self,
        tenant_id: str,
        requested: List[str],
        quota: Optional[SessionQuota] = None
    ) -> Dict:
        """
        Negotiate capabilities and create a new session.
        
        Args:
            tenant_id: Tenant identifier
            requested: List of requested capabilities
            quota: Optional custom quota (defaults to default_quota)
        
        Returns:
            Dictionary with negotiation results:
            - session_id: New session ID
            - granted: List of granted capabilities
            - denied: List of denied capabilities
            - quota: Resource quotas
        """
        # Generate unique session ID
        session_id = self._generate_session_id()
        
        # Determine granted capabilities
        # For now, grant all valid requested capabilities
        # In production, this would check tenant permissions
        granted = set()
        denied = []
        
        for cap in requested:
            if cap in self.ALL_CAPABILITIES:
                granted.add(cap)
            else:
                denied.append(cap)
        
        # Create session
        session_quota = quota or self.default_quota
        session = Session(
            session_id=session_id,
            tenant_id=tenant_id,
            granted_caps=granted,
            quota=session_quota
        )
        
        # Register session
        self.sessions[session_id] = session
        
        if tenant_id not in self.tenant_sessions:
            self.tenant_sessions[tenant_id] = set()
        self.tenant_sessions[tenant_id].add(session_id)
        
        return {
            "session_id": session_id,
            "granted": list(granted),
            "denied": denied,
            "quota": {
                "max_logical_qubits": session_quota.max_logical_qubits,
                "max_channels": session_quota.max_channels,
                "max_jobs": session_quota.max_jobs,
                "max_physical_qubits": session_quota.max_physical_qubits,
            }
        }
    
    def get_session(self, session_id: str) -> Session:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session object
        
        Raises:
            KeyError: If session not found
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session '{session_id}' not found")
        
        return self.sessions[session_id]
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate that a session exists and is active.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session is valid
        """
        return session_id in self.sessions
    
    def check_capabilities(self, session_id: str, required: List[str]) -> Dict:
        """
        Check if session has required capabilities.
        
        Args:
            session_id: Session identifier
            required: List of required capabilities
        
        Returns:
            Dictionary with:
            - has_all: True if all capabilities present
            - missing: List of missing capabilities
        
        Raises:
            KeyError: If session not found
        """
        session = self.get_session(session_id)
        missing = session.missing_capabilities(required)
        
        return {
            "has_all": len(missing) == 0,
            "missing": missing
        }
    
    def register_job(self, session_id: str, job_id: str):
        """
        Register a job with a session.
        
        Args:
            session_id: Session identifier
            job_id: Job identifier
        
        Raises:
            KeyError: If session not found
            RuntimeError: If quota exceeded
        """
        session = self.get_session(session_id)
        
        if not session.can_create_job():
            raise RuntimeError(
                f"Job quota exceeded: {len(session.active_jobs)}/{session.quota.max_jobs}"
            )
        
        session.active_jobs.add(job_id)
    
    def unregister_job(self, session_id: str, job_id: str):
        """
        Unregister a job from a session.
        
        Args:
            session_id: Session identifier
            job_id: Job identifier
        """
        if session_id in self.sessions:
            self.sessions[session_id].active_jobs.discard(job_id)
    
    def register_qubits(self, session_id: str, vq_ids: List[str]):
        """
        Register allocated qubits with a session.
        
        Args:
            session_id: Session identifier
            vq_ids: List of virtual qubit IDs
        
        Raises:
            KeyError: If session not found
            RuntimeError: If quota exceeded
        """
        session = self.get_session(session_id)
        
        if not session.can_allocate_qubits(len(vq_ids)):
            raise RuntimeError(
                f"Qubit quota exceeded: {len(session.allocated_qubits) + len(vq_ids)}/"
                f"{session.quota.max_logical_qubits}"
            )
        
        session.allocated_qubits.update(vq_ids)
    
    def unregister_qubits(self, session_id: str, vq_ids: List[str]):
        """
        Unregister qubits from a session.
        
        Args:
            session_id: Session identifier
            vq_ids: List of virtual qubit IDs
        """
        if session_id in self.sessions:
            for vq_id in vq_ids:
                self.sessions[session_id].allocated_qubits.discard(vq_id)
    
    def register_channel(self, session_id: str, channel_id: str):
        """
        Register an open channel with a session.
        
        Args:
            session_id: Session identifier
            channel_id: Channel identifier
        
        Raises:
            KeyError: If session not found
            RuntimeError: If quota exceeded
        """
        session = self.get_session(session_id)
        
        if not session.can_open_channel():
            raise RuntimeError(
                f"Channel quota exceeded: {len(session.open_channels)}/"
                f"{session.quota.max_channels}"
            )
        
        session.open_channels.add(channel_id)
    
    def unregister_channel(self, session_id: str, channel_id: str):
        """
        Unregister a channel from a session.
        
        Args:
            session_id: Session identifier
            channel_id: Channel identifier
        """
        if session_id in self.sessions:
            self.sessions[session_id].open_channels.discard(channel_id)
    
    def close_session(self, session_id: str):
        """
        Close a session and clean up resources.
        
        Args:
            session_id: Session identifier
        """
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # Remove from tenant tracking
        if session.tenant_id in self.tenant_sessions:
            self.tenant_sessions[session.tenant_id].discard(session_id)
            if not self.tenant_sessions[session.tenant_id]:
                del self.tenant_sessions[session.tenant_id]
        
        # Remove session
        del self.sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        Get session information.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with session details
        
        Raises:
            KeyError: If session not found
        """
        session = self.get_session(session_id)
        
        return {
            "session_id": session.session_id,
            "tenant_id": session.tenant_id,
            "capabilities": list(session.granted_caps),
            "quota": {
                "max_logical_qubits": session.quota.max_logical_qubits,
                "max_channels": session.quota.max_channels,
                "max_jobs": session.quota.max_jobs,
            },
            "usage": {
                "active_jobs": len(session.active_jobs),
                "allocated_qubits": len(session.allocated_qubits),
                "open_channels": len(session.open_channels),
            },
            "created_at": session.created_at,
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"sess_{secrets.token_hex(8)}"
