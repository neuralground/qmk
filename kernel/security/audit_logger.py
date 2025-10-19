"""
Audit Logging System

Provides comprehensive audit logging for security-relevant events.
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication & Authorization
    SESSION_CREATED = "session_created"
    SESSION_CLOSED = "session_closed"
    CAPABILITY_GRANTED = "capability_granted"
    CAPABILITY_DENIED = "capability_denied"
    
    # Resource Operations
    RESOURCE_ALLOCATED = "resource_allocated"
    RESOURCE_FREED = "resource_freed"
    RESOURCE_ACCESS_DENIED = "resource_access_denied"
    
    # Job Operations
    JOB_SUBMITTED = "job_submitted"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    
    # Security Events
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID_HANDLE = "invalid_handle"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    TENANT_CREATED = "tenant_created"
    TENANT_DEACTIVATED = "tenant_deactivated"
    
    # System Events
    CHECKPOINT_CREATED = "checkpoint_created"
    MIGRATION_STARTED = "migration_started"
    MIGRATION_COMPLETED = "migration_completed"
    ROLLBACK_PERFORMED = "rollback_performed"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Represents an audit event.
    
    Attributes:
        event_id: Unique event identifier
        event_type: Type of event
        severity: Event severity
        timestamp: Event timestamp
        tenant_id: Associated tenant
        session_id: Associated session (if applicable)
        user_id: Associated user (if applicable)
        resource_id: Associated resource (if applicable)
        action: Action performed
        result: Result of action (success/failure)
        details: Additional event details
        metadata: Extra metadata
    """
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: float
    tenant_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    action: str = ""
    result: str = "success"
    details: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "result": self.result,
            "details": self.details,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Provides:
    - Event logging with severity levels
    - Filtering and querying
    - Export capabilities
    - Retention management
    """
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize audit logger.
        
        Args:
            max_events: Maximum events to keep in memory
        """
        self.max_events = max_events
        self.events: List[AuditEvent] = []
        self.event_counter = 0
    
    def log_event(
        self,
        event_type: AuditEventType,
        tenant_id: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "",
        result: str = "success",
        details: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            tenant_id: Tenant identifier
            severity: Event severity
            session_id: Optional session identifier
            user_id: Optional user identifier
            resource_id: Optional resource identifier
            action: Action description
            result: Result (success/failure/etc.)
            details: Additional details
            metadata: Extra metadata
        
        Returns:
            Created AuditEvent
        """
        event_id = f"audit_{self.event_counter}"
        self.event_counter += 1
        
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=time.time(),
            tenant_id=tenant_id,
            session_id=session_id,
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {},
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        # Enforce max events limit
        if len(self.events) > self.max_events:
            self.events.pop(0)
        
        return event
    
    def query_events(
        self,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Args:
            tenant_id: Filter by tenant
            session_id: Filter by session
            event_type: Filter by event type
            severity: Filter by severity
            start_time: Filter by start timestamp
            end_time: Filter by end timestamp
            limit: Maximum events to return
        
        Returns:
            List of matching AuditEvent objects
        """
        results = []
        
        for event in reversed(self.events):  # Most recent first
            if len(results) >= limit:
                break
            
            # Apply filters
            if tenant_id and event.tenant_id != tenant_id:
                continue
            
            if session_id and event.session_id != session_id:
                continue
            
            if event_type and event.event_type != event_type:
                continue
            
            if severity and event.severity != severity:
                continue
            
            if start_time and event.timestamp < start_time:
                continue
            
            if end_time and event.timestamp > end_time:
                continue
            
            results.append(event)
        
        return results
    
    def get_event_stats(self) -> Dict:
        """
        Get statistics about audit events.
        
        Returns:
            Dictionary with event statistics
        """
        total = len(self.events)
        
        by_type = {}
        by_severity = {}
        by_tenant = {}
        
        for event in self.events:
            # Count by type
            event_type_str = event.event_type.value
            by_type[event_type_str] = by_type.get(event_type_str, 0) + 1
            
            # Count by severity
            severity_str = event.severity.value
            by_severity[severity_str] = by_severity.get(severity_str, 0) + 1
            
            # Count by tenant
            by_tenant[event.tenant_id] = by_tenant.get(event.tenant_id, 0) + 1
        
        return {
            "total_events": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "by_tenant": by_tenant
        }
    
    def export_events(
        self,
        format: str = "json",
        tenant_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """
        Export audit events.
        
        Args:
            format: Export format (json, csv)
            tenant_id: Filter by tenant
            start_time: Filter by start time
            end_time: Filter by end time
        
        Returns:
            Exported data as string
        """
        events = self.query_events(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            limit=len(self.events)
        )
        
        if format == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        elif format == "csv":
            # Simple CSV export
            lines = ["event_id,event_type,severity,timestamp,tenant_id,session_id,result"]
            for event in events:
                lines.append(
                    f"{event.event_id},{event.event_type.value},"
                    f"{event.severity.value},{event.timestamp},"
                    f"{event.tenant_id},{event.session_id or ''},"
                    f"{event.result}"
                )
            return "\n".join(lines)
        
        raise ValueError(f"Unsupported format: {format}")
    
    def clear_events(self, tenant_id: Optional[str] = None):
        """
        Clear audit events.
        
        Args:
            tenant_id: Only clear events for specific tenant (None = all)
        """
        if tenant_id:
            self.events = [e for e in self.events if e.tenant_id != tenant_id]
        else:
            self.events.clear()
