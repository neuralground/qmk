"""
Linear Type System for Quantum Resources

Implements linear types to enforce use-once semantics for quantum resources.
Prevents resource aliasing, use-after-free, and double-free bugs.

Linear types ensure that quantum resources (qubits, channels, events) are:
- Used exactly once (no-cloning theorem)
- Not aliased (single owner)
- Automatically cleaned up (no leaks)

Research Foundation:
- Wadler (1990): "Linear Types Can Change the World"
- Altenkirch & Grattage (2005): "A Functional Quantum Programming Language"
- Green et al. (2013): "Quipper: A Scalable Quantum Programming Language"
"""

import time
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ResourceState(Enum):
    """State of a linear resource."""
    ALLOCATED = "allocated"      # Resource allocated, not yet used
    CONSUMED = "consumed"         # Resource consumed (measured, freed, etc.)
    MOVED = "moved"              # Resource moved to another handle
    INVALIDATED = "invalidated"  # Resource invalidated (error, etc.)


class LinearityViolationType(Enum):
    """Types of linearity violations."""
    USE_AFTER_CONSUME = "use_after_consume"    # Using consumed resource
    DOUBLE_CONSUME = "double_consume"          # Consuming twice
    RESOURCE_LEAK = "resource_leak"            # Resource not consumed
    ALIASING = "aliasing"                      # Multiple references
    MOVED_RESOURCE = "moved_resource"          # Using moved resource


class LinearityViolation(Exception):
    """Raised when linearity constraints are violated."""
    
    def __init__(self, message: str, violation_type: LinearityViolationType, details: Dict):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details


@dataclass
class LinearHandle:
    """
    Linear handle for quantum resources.
    
    A linear handle can be used exactly once. After consumption,
    the handle becomes invalid and cannot be reused.
    
    Attributes:
        handle_id: Unique handle identifier
        resource_type: Type of resource (VQ, CH, EV)
        resource_id: ID of underlying resource
        tenant_id: Owning tenant
        state: Current state of handle
        created_at: Creation timestamp
        consumed_at: Consumption timestamp (if consumed)
        consumed_by: Operation that consumed the handle
        metadata: Additional metadata
    """
    handle_id: str
    resource_type: str
    resource_id: str
    tenant_id: str
    state: ResourceState = ResourceState.ALLOCATED
    created_at: float = field(default_factory=time.time)
    consumed_at: Optional[float] = None
    consumed_by: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if handle is valid (can be used)."""
        return self.state == ResourceState.ALLOCATED
    
    def is_consumed(self) -> bool:
        """Check if handle has been consumed."""
        return self.state == ResourceState.CONSUMED
    
    def consume(self, operation: str):
        """
        Consume the handle.
        
        Args:
            operation: Operation consuming the handle
        
        Raises:
            LinearityViolation: If handle already consumed
        """
        if self.state == ResourceState.CONSUMED:
            raise LinearityViolation(
                f"Handle {self.handle_id} already consumed by {self.consumed_by}",
                LinearityViolationType.DOUBLE_CONSUME,
                {
                    "handle_id": self.handle_id,
                    "previous_operation": self.consumed_by,
                    "attempted_operation": operation
                }
            )
        
        if self.state == ResourceState.MOVED:
            raise LinearityViolation(
                f"Handle {self.handle_id} has been moved",
                LinearityViolationType.MOVED_RESOURCE,
                {
                    "handle_id": self.handle_id,
                    "attempted_operation": operation
                }
            )
        
        if self.state != ResourceState.ALLOCATED:
            raise LinearityViolation(
                f"Handle {self.handle_id} is not in valid state: {self.state}",
                LinearityViolationType.USE_AFTER_CONSUME,
                {
                    "handle_id": self.handle_id,
                    "state": self.state.value,
                    "attempted_operation": operation
                }
            )
        
        self.state = ResourceState.CONSUMED
        self.consumed_at = time.time()
        self.consumed_by = operation
    
    def move(self) -> str:
        """
        Move the handle (transfer ownership).
        
        Returns:
            New handle ID
        """
        if not self.is_valid():
            raise LinearityViolation(
                f"Cannot move invalid handle {self.handle_id}",
                LinearityViolationType.USE_AFTER_CONSUME,
                {"handle_id": self.handle_id, "state": self.state.value}
            )
        
        self.state = ResourceState.MOVED
        return self.handle_id
    
    def invalidate(self):
        """Invalidate the handle (error recovery)."""
        self.state = ResourceState.INVALIDATED
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "handle_id": self.handle_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "tenant_id": self.tenant_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "consumed_at": self.consumed_at,
            "consumed_by": self.consumed_by,
            "is_valid": self.is_valid()
        }


class LinearTypeSystem:
    """
    Manages linear types and enforces linearity constraints.
    
    Provides:
    - Handle creation and tracking
    - Consumption enforcement
    - Leak detection
    - Aliasing prevention
    """
    
    def __init__(self, audit_logger=None):
        """
        Initialize linear type system.
        
        Args:
            audit_logger: Optional AuditLogger for violations
        """
        self.audit_logger = audit_logger
        
        # Handle storage: handle_id -> LinearHandle
        self.handles: Dict[str, LinearHandle] = {}
        
        # Resource tracking: resource_id -> handle_id
        self.resource_handles: Dict[str, str] = {}
        
        # Tenant handles: tenant_id -> set of handle_ids
        self.tenant_handles: Dict[str, Set[str]] = {}
        
        # Statistics
        self.handles_created = 0
        self.handles_consumed = 0
        self.linearity_violations = 0
        self.resource_leaks = 0
    
    def create_handle(
        self,
        resource_type: str,
        resource_id: str,
        tenant_id: str,
        metadata: Optional[Dict] = None
    ) -> LinearHandle:
        """
        Create a new linear handle.
        
        Args:
            resource_type: Type of resource (VQ, CH, EV)
            resource_id: ID of underlying resource
            tenant_id: Owning tenant
            metadata: Optional metadata
        
        Returns:
            LinearHandle
        
        Raises:
            LinearityViolation: If resource already has a handle (aliasing)
        """
        # Check for aliasing
        if resource_id in self.resource_handles:
            existing_handle_id = self.resource_handles[resource_id]
            existing_handle = self.handles[existing_handle_id]
            
            if existing_handle.is_valid():
                self.linearity_violations += 1
                
                if self.audit_logger:
                    self.audit_logger.log(
                        "linearity_violation",
                        severity="critical",
                        tenant_id=tenant_id,
                        details={
                            "violation_type": LinearityViolationType.ALIASING.value,
                            "resource_id": resource_id,
                            "existing_handle": existing_handle_id
                        }
                    )
                
                raise LinearityViolation(
                    f"Resource {resource_id} already has valid handle {existing_handle_id}",
                    LinearityViolationType.ALIASING,
                    {
                        "resource_id": resource_id,
                        "existing_handle": existing_handle_id
                    }
                )
        
        # Generate handle ID
        handle_id = f"lin_{self.handles_created}_{resource_type}_{resource_id}"
        
        # Create handle
        handle = LinearHandle(
            handle_id=handle_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            metadata=metadata or {}
        )
        
        # Store handle
        self.handles[handle_id] = handle
        self.resource_handles[resource_id] = handle_id
        
        if tenant_id not in self.tenant_handles:
            self.tenant_handles[tenant_id] = set()
        self.tenant_handles[tenant_id].add(handle_id)
        
        self.handles_created += 1
        
        # Audit log
        if self.audit_logger:
            self.audit_logger.log(
                "linear_handle_created",
                tenant_id=tenant_id,
                details={
                    "handle_id": handle_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            )
        
        return handle
    
    def consume_handle(self, handle_id: str, operation: str):
        """
        Consume a linear handle.
        
        Args:
            handle_id: Handle to consume
            operation: Operation consuming the handle
        
        Raises:
            LinearityViolation: If handle invalid or already consumed
        """
        if handle_id not in self.handles:
            raise KeyError(f"Handle {handle_id} not found")
        
        handle = self.handles[handle_id]
        
        try:
            handle.consume(operation)
            self.handles_consumed += 1
            
            # Remove from resource tracking
            if handle.resource_id in self.resource_handles:
                del self.resource_handles[handle.resource_id]
            
            # Audit log
            if self.audit_logger:
                self.audit_logger.log(
                    "linear_handle_consumed",
                    tenant_id=handle.tenant_id,
                    details={
                        "handle_id": handle_id,
                        "resource_id": handle.resource_id,
                        "operation": operation
                    }
                )
        
        except LinearityViolation as e:
            self.linearity_violations += 1
            
            if self.audit_logger:
                self.audit_logger.log(
                    "linearity_violation",
                    severity="critical",
                    tenant_id=handle.tenant_id,
                    details={
                        "violation_type": e.violation_type.value,
                        "handle_id": handle_id,
                        "operation": operation,
                        **e.details
                    }
                )
            
            raise
    
    def check_handle(self, handle_id: str) -> bool:
        """
        Check if handle is valid.
        
        Args:
            handle_id: Handle to check
        
        Returns:
            True if valid, False otherwise
        """
        if handle_id not in self.handles:
            return False
        
        return self.handles[handle_id].is_valid()
    
    def get_handle(self, handle_id: str) -> Optional[LinearHandle]:
        """Get handle by ID."""
        return self.handles.get(handle_id)
    
    def get_resource_handle(self, resource_id: str) -> Optional[LinearHandle]:
        """Get handle for a resource."""
        handle_id = self.resource_handles.get(resource_id)
        if handle_id:
            return self.handles.get(handle_id)
        return None
    
    def detect_leaks(self, tenant_id: Optional[str] = None) -> Dict[str, LinearHandle]:
        """
        Detect resource leaks (unconsumed handles).
        
        Args:
            tenant_id: Optional tenant to check (None = all tenants)
        
        Returns:
            Dictionary of leaked handles
        """
        leaks = {}
        
        for handle_id, handle in self.handles.items():
            if tenant_id and handle.tenant_id != tenant_id:
                continue
            
            if handle.state == ResourceState.ALLOCATED:
                # Check if handle is old (potential leak)
                age = time.time() - handle.created_at
                if age > 60:  # 60 seconds threshold
                    leaks[handle_id] = handle
                    self.resource_leaks += 1
        
        if leaks and self.audit_logger:
            self.audit_logger.log(
                "resource_leaks_detected",
                severity="warning",
                tenant_id=tenant_id or "all",
                details={
                    "leak_count": len(leaks),
                    "leaked_handles": list(leaks.keys())
                }
            )
        
        return leaks
    
    def cleanup_consumed_handles(self) -> int:
        """
        Remove consumed handles from tracking.
        
        Returns:
            Number of handles removed
        """
        to_remove = [
            hid for hid, handle in self.handles.items()
            if handle.is_consumed()
        ]
        
        for hid in to_remove:
            handle = self.handles[hid]
            
            # Remove from tenant tracking
            if handle.tenant_id in self.tenant_handles:
                self.tenant_handles[handle.tenant_id].discard(hid)
            
            del self.handles[hid]
        
        return len(to_remove)
    
    def get_tenant_handles(
        self,
        tenant_id: str,
        valid_only: bool = True
    ) -> Dict[str, LinearHandle]:
        """
        Get all handles for a tenant.
        
        Args:
            tenant_id: Tenant ID
            valid_only: Only return valid handles
        
        Returns:
            Dictionary of handles
        """
        handle_ids = self.tenant_handles.get(tenant_id, set())
        handles = {hid: self.handles[hid] for hid in handle_ids if hid in self.handles}
        
        if valid_only:
            handles = {hid: h for hid, h in handles.items() if h.is_valid()}
        
        return handles
    
    def get_statistics(self) -> Dict:
        """
        Get linear type system statistics.
        
        Returns:
            Dictionary with statistics
        """
        valid_handles = sum(1 for h in self.handles.values() if h.is_valid())
        consumed_handles = sum(1 for h in self.handles.values() if h.is_consumed())
        
        return {
            "handles_created": self.handles_created,
            "handles_consumed": self.handles_consumed,
            "active_handles": valid_handles,
            "consumed_handles": consumed_handles,
            "total_handles": len(self.handles),
            "linearity_violations": self.linearity_violations,
            "resource_leaks": self.resource_leaks
        }
    
    def verify_linearity(self) -> tuple[bool, list[str]]:
        """
        Verify linearity constraints.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # Check for aliasing
        resource_counts = {}
        for handle in self.handles.values():
            if handle.is_valid():
                rid = handle.resource_id
                resource_counts[rid] = resource_counts.get(rid, 0) + 1
        
        for rid, count in resource_counts.items():
            if count > 1:
                violations.append(
                    f"Resource {rid} has {count} valid handles (aliasing)"
                )
        
        # Check for leaks
        leaks = self.detect_leaks()
        if leaks:
            violations.append(
                f"Found {len(leaks)} potential resource leaks"
            )
        
        return len(violations) == 0, violations
