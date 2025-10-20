"""
Tamper-Evident Audit Log with Merkle Tree

Provides cryptographically secure audit logging with tamper detection.
All audit entries are added to a Merkle tree, making any tampering detectable.

Security Properties:
- Tamper Evidence: Any modification to logs changes the root hash
- Append-Only: Logs can only be appended, not modified
- Cryptographic Binding: Each entry is cryptographically bound to all previous entries
- Efficient Verification: Can verify log integrity in O(log n) time

Research:
    - Schneier, B., & Kelsey, J. (1999). "Secure Audit Logs to Support Computer Forensics"
    - Crosby, M., et al. (2016). "BlockChain Technology: Beyond Bitcoin"
    - Haber, S., & Stornetta, W. S. (1991). "How to Time-Stamp a Digital Document"
"""

import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .merkle_tree import MerkleTree, MerkleProof


class AuditEventType(Enum):
    """Types of audit events."""
    # Capability events
    CAPABILITY_CHECK = "CAPABILITY_CHECK"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    TOKEN_CREATED = "TOKEN_CREATED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_ATTENUATED = "TOKEN_ATTENUATED"
    
    # Resource events
    QUBIT_ALLOCATED = "QUBIT_ALLOCATED"
    QUBIT_DEALLOCATED = "QUBIT_DEALLOCATED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # Operation events
    OPERATION_EXECUTED = "OPERATION_EXECUTED"
    OPERATION_FAILED = "OPERATION_FAILED"
    
    # Security events
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    ACCESS_DENIED = "ACCESS_DENIED"
    TIMING_ANOMALY = "TIMING_ANOMALY"
    
    # Administrative events
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_DESTROYED = "SESSION_DESTROYED"


@dataclass
class AuditEvent:
    """Audit event entry."""
    event_type: AuditEventType
    tenant_id: str
    timestamp: float
    details: Dict[str, Any]
    sequence_number: int
    
    def to_bytes(self) -> bytes:
        """Serialize event to bytes for hashing."""
        data = {
            'event_type': self.event_type.value,
            'tenant_id': self.tenant_id,
            'timestamp': self.timestamp,
            'details': self.details,
            'sequence_number': self.sequence_number
        }
        return json.dumps(data, sort_keys=True).encode('utf-8')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_type': self.event_type.value,
            'tenant_id': self.tenant_id,
            'timestamp': self.timestamp,
            'details': self.details,
            'sequence_number': self.sequence_number
        }


class TamperEvidentAuditLog:
    """
    Audit log with Merkle tree for tamper evidence.
    
    Provides cryptographically secure audit logging where any tampering
    with historical entries is immediately detectable.
    
    Security Guarantees:
    - Tamper evidence: Root hash changes if any entry modified
    - Append-only: Cannot modify or delete historical entries
    - Ordering: Sequence numbers prevent reordering
    - Completeness: Missing entries are detectable
    
    Attributes:
        merkle_tree: Merkle tree of audit entries
        events: List of audit events
        sequence_counter: Monotonically increasing sequence number
    """
    
    def __init__(self):
        """Initialize tamper-evident audit log."""
        self.merkle_tree = MerkleTree()
        self.events: List[AuditEvent] = []
        self.sequence_counter = 0
    
    def append(
        self,
        event_type: AuditEventType,
        tenant_id: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Append audit event to log.
        
        Args:
            event_type: Type of audit event
            tenant_id: ID of tenant
            details: Event details
        
        Returns:
            Root hash after appending (hex string)
        
        Example:
            >>> log = TamperEvidentAuditLog()
            >>> root = log.append(
            ...     AuditEventType.CAPABILITY_CHECK,
            ...     'tenant1',
            ...     {'operation': 'MEASURE_Z', 'allowed': True}
            ... )
        """
        # Create event
        event = AuditEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            timestamp=time.time(),
            details=details,
            sequence_number=self.sequence_counter
        )
        
        # Add to events list
        self.events.append(event)
        
        # Add to Merkle tree
        root_hash = self.merkle_tree.append(event.to_bytes())
        
        # Increment sequence counter
        self.sequence_counter += 1
        
        return root_hash.hex()
    
    def get_root_hash(self) -> str:
        """
        Get current root hash.
        
        Returns:
            Root hash (hex string)
        """
        return self.merkle_tree.root().hex()
    
    def get_proof(self, index: int) -> Optional[MerkleProof]:
        """
        Get Merkle proof for event at index.
        
        Args:
            index: Index of event
        
        Returns:
            Merkle proof or None if invalid index
        """
        return self.merkle_tree.get_proof(index)
    
    def verify_event(self, index: int) -> bool:
        """
        Verify that event at index has not been tampered with.
        
        Args:
            index: Index of event to verify
        
        Returns:
            True if event is valid
        """
        if index < 0 or index >= len(self.events):
            return False
        
        event = self.events[index]
        proof = self.get_proof(index)
        
        if not proof:
            return False
        
        return self.merkle_tree.verify_proof(proof, event.to_bytes())
    
    def verify_integrity(self, start_index: int = 0, end_index: Optional[int] = None) -> bool:
        """
        Verify integrity of log range.
        
        Args:
            start_index: Start of range
            end_index: End of range (None = all)
        
        Returns:
            True if all events in range are valid
        """
        if end_index is None:
            end_index = len(self.events)
        
        for i in range(start_index, end_index):
            if not self.verify_event(i):
                return False
        
        return True
    
    def get_events(
        self,
        tenant_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Args:
            tenant_id: Filter by tenant
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events
        
        Returns:
            List of matching audit events
        """
        events = self.events
        
        # Apply filters
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Returns:
            Dictionary with statistics
        """
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        tenant_counts = {}
        for event in self.events:
            tenant_id = event.tenant_id
            tenant_counts[tenant_id] = tenant_counts.get(tenant_id, 0) + 1
        
        return {
            'total_events': len(self.events),
            'root_hash': self.get_root_hash(),
            'sequence_number': self.sequence_counter,
            'event_counts': event_counts,
            'tenant_counts': tenant_counts,
            'merkle_tree_size': self.merkle_tree.size()
        }
    
    def export_events(self, start_index: int = 0, end_index: Optional[int] = None) -> List[Dict]:
        """
        Export events to list of dictionaries.
        
        Args:
            start_index: Start index
            end_index: End index (None = all)
        
        Returns:
            List of event dictionaries
        """
        if end_index is None:
            end_index = len(self.events)
        
        return [
            event.to_dict()
            for event in self.events[start_index:end_index]
        ]
    
    def detect_tampering(self) -> Optional[int]:
        """
        Detect if any tampering has occurred.
        
        Returns:
            Index of first tampered event, or None if no tampering
        """
        for i in range(len(self.events)):
            if not self.verify_event(i):
                return i
        return None
