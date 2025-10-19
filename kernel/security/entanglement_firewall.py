"""
Entanglement Firewall

Prevents unauthorized cross-tenant entanglement by tracking all entanglement
relationships and enforcing channel-based authorization for cross-tenant operations.

This is a critical quantum-specific security feature that prevents information
leakage through entanglement.

Research Foundation:
- Pirandola et al. (2017): "Theory of Channel Simulation and Bounds for Private Communication"
- Broadbent et al. (2009): "Universal Blind Quantum Computation"
"""

import time
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class FirewallViolationType(Enum):
    """Types of firewall violations."""
    UNAUTHORIZED_CROSS_TENANT = "unauthorized_cross_tenant"
    MISSING_CHANNEL = "missing_channel"
    INVALID_CHANNEL = "invalid_channel"
    REVOKED_CHANNEL = "revoked_channel"
    EXPIRED_CHANNEL = "expired_channel"
    CHANNEL_QUOTA_EXCEEDED = "channel_quota_exceeded"


@dataclass
class EntanglementEdge:
    """
    Represents an entanglement relationship between two qubits.
    
    Attributes:
        vq1: First virtual qubit ID
        vq2: Second virtual qubit ID
        tenant1: Tenant owning vq1
        tenant2: Tenant owning vq2
        channel_id: Channel ID if cross-tenant (None if same tenant)
        created_at: When entanglement was created
        gate_type: Gate that created entanglement (CNOT, CZ, etc.)
    """
    vq1: str
    vq2: str
    tenant1: str
    tenant2: str
    channel_id: Optional[str]
    created_at: float
    gate_type: str
    
    def is_cross_tenant(self) -> bool:
        """Check if this is cross-tenant entanglement."""
        return self.tenant1 != self.tenant2
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "vq1": self.vq1,
            "vq2": self.vq2,
            "tenant1": self.tenant1,
            "tenant2": self.tenant2,
            "channel_id": self.channel_id,
            "created_at": self.created_at,
            "gate_type": self.gate_type,
            "is_cross_tenant": self.is_cross_tenant()
        }


@dataclass
class Channel:
    """
    Authorized channel for cross-tenant entanglement.
    
    Requires agreement from both tenants.
    """
    channel_id: str
    tenant_a: str
    tenant_b: str
    
    # Authorization
    authorized_by_a: bool = True
    authorized_by_b: bool = True
    
    # Constraints
    max_entanglements: int = 1000
    entanglements_used: int = 0
    
    # Lifecycle
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_active: bool = True
    is_revoked: bool = False
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if channel is valid."""
        if not self.is_active or self.is_revoked:
            return False
        
        if self.expires_at and time.time() > self.expires_at:
            return False
        
        if self.entanglements_used >= self.max_entanglements:
            return False
        
        return True
    
    def authorizes_tenants(self, tenant1: str, tenant2: str) -> bool:
        """Check if channel authorizes these specific tenants (ignoring validity)."""
        # Check both directions
        return ((tenant1 == self.tenant_a and tenant2 == self.tenant_b) or
                (tenant1 == self.tenant_b and tenant2 == self.tenant_a))
    
    def authorizes(self, tenant1: str, tenant2: str) -> bool:
        """Check if channel authorizes entanglement between tenants (including validity)."""
        if not self.is_valid():
            return False
        
        return self.authorizes_tenants(tenant1, tenant2)
    
    def use(self) -> bool:
        """
        Use one entanglement from quota.
        
        Returns:
            True if successful, False if quota exceeded
        """
        if not self.is_valid():
            return False
        
        if self.entanglements_used >= self.max_entanglements:
            return False
        
        self.entanglements_used += 1
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "channel_id": self.channel_id,
            "tenant_a": self.tenant_a,
            "tenant_b": self.tenant_b,
            "authorized_by_a": self.authorized_by_a,
            "authorized_by_b": self.authorized_by_b,
            "max_entanglements": self.max_entanglements,
            "entanglements_used": self.entanglements_used,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "is_revoked": self.is_revoked,
            "is_valid": self.is_valid()
        }


class EntanglementFirewallViolation(Exception):
    """Raised when firewall detects unauthorized cross-tenant entanglement."""
    
    def __init__(self, message: str, violation_type: FirewallViolationType, details: Dict):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details


class EntanglementGraph:
    """
    Tracks all entanglement relationships in the system.
    
    Enforces the critical invariant:
        No cross-tenant entanglement without explicit authorized channel.
    
    This is the core of the entanglement firewall.
    """
    
    def __init__(self, audit_logger=None):
        """
        Initialize entanglement graph.
        
        Args:
            audit_logger: Optional AuditLogger for security events
        """
        # Graph structure: vq_id -> set of entangled vq_ids
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Qubit ownership: vq_id -> tenant_id
        self.qubit_owners: Dict[str, str] = {}
        
        # Entanglement edges with metadata
        self.edges: Dict[Tuple[str, str], EntanglementEdge] = {}
        
        # Authorized channels
        self.channels: Dict[str, Channel] = {}
        
        # Audit logger
        self.audit_logger = audit_logger
        
        # Statistics
        self.total_entanglements = 0
        self.cross_tenant_entanglements = 0
        self.firewall_violations = 0
    
    def register_qubit(self, vq_id: str, tenant_id: str):
        """
        Register a qubit with its owner.
        
        Args:
            vq_id: Virtual qubit ID
            tenant_id: Owning tenant
        """
        self.qubit_owners[vq_id] = tenant_id
        
        if self.audit_logger:
            self.audit_logger.log(
                "qubit_registered",
                tenant_id=tenant_id,
                details={"vq_id": vq_id}
            )
    
    def unregister_qubit(self, vq_id: str):
        """
        Unregister a qubit (e.g., after measurement or deallocation).
        
        Args:
            vq_id: Virtual qubit ID
        """
        # Remove all entanglements involving this qubit
        if vq_id in self.graph:
            for other_vq in self.graph[vq_id]:
                self.graph[other_vq].discard(vq_id)
                
                # Remove edge
                edge_key = self._edge_key(vq_id, other_vq)
                if edge_key in self.edges:
                    del self.edges[edge_key]
            
            del self.graph[vq_id]
        
        # Remove ownership
        if vq_id in self.qubit_owners:
            del self.qubit_owners[vq_id]
    
    def add_entanglement(
        self,
        vq1: str,
        vq2: str,
        gate_type: str,
        channel: Optional[Channel] = None
    ) -> None:
        """
        Add entanglement between two qubits.
        
        This is the critical security check point!
        
        Args:
            vq1: First virtual qubit ID
            vq2: Second virtual qubit ID
            gate_type: Gate creating entanglement (CNOT, CZ, etc.)
            channel: Optional channel for cross-tenant entanglement
        
        Raises:
            EntanglementFirewallViolation: If unauthorized cross-tenant entanglement
        """
        # Get qubit owners
        tenant1 = self.qubit_owners.get(vq1)
        tenant2 = self.qubit_owners.get(vq2)
        
        if tenant1 is None or tenant2 is None:
            raise ValueError(f"Qubits not registered: {vq1}, {vq2}")
        
        # Check if cross-tenant
        is_cross_tenant = (tenant1 != tenant2)
        
        if is_cross_tenant:
            # Cross-tenant entanglement requires channel
            if channel is None:
                self.firewall_violations += 1
                
                if self.audit_logger:
                    self.audit_logger.log(
                        "firewall_violation",
                        severity="critical",
                        details={
                            "violation_type": FirewallViolationType.MISSING_CHANNEL.value,
                            "vq1": vq1,
                            "vq2": vq2,
                            "tenant1": tenant1,
                            "tenant2": tenant2,
                            "gate_type": gate_type
                        }
                    )
                
                raise EntanglementFirewallViolation(
                    f"Cross-tenant entanglement requires channel: "
                    f"{vq1} ({tenant1}) ↔ {vq2} ({tenant2})",
                    FirewallViolationType.MISSING_CHANNEL,
                    {
                        "vq1": vq1,
                        "vq2": vq2,
                        "tenant1": tenant1,
                        "tenant2": tenant2
                    }
                )
            
            # Verify channel authorizes these tenants
            if not channel.authorizes_tenants(tenant1, tenant2):
                self.firewall_violations += 1
                
                if self.audit_logger:
                    self.audit_logger.log(
                        "firewall_violation",
                        severity="critical",
                        details={
                            "violation_type": FirewallViolationType.INVALID_CHANNEL.value,
                            "vq1": vq1,
                            "vq2": vq2,
                            "tenant1": tenant1,
                            "tenant2": tenant2,
                            "channel_id": channel.channel_id
                        }
                    )
                
                raise EntanglementFirewallViolation(
                    f"Channel does not authorize {tenant1} ↔ {tenant2}",
                    FirewallViolationType.INVALID_CHANNEL,
                    {"channel_id": channel.channel_id}
                )
            
            # Use channel quota
            if not channel.use():
                self.firewall_violations += 1
                
                if self.audit_logger:
                    self.audit_logger.log(
                        "firewall_violation",
                        severity="error",
                        details={
                            "violation_type": FirewallViolationType.CHANNEL_QUOTA_EXCEEDED.value,
                            "channel_id": channel.channel_id,
                            "used": channel.entanglements_used,
                            "max": channel.max_entanglements
                        }
                    )
                
                raise EntanglementFirewallViolation(
                    f"Channel quota exceeded: {channel.entanglements_used}/{channel.max_entanglements}",
                    FirewallViolationType.CHANNEL_QUOTA_EXCEEDED,
                    {"channel_id": channel.channel_id}
                )
            
            self.cross_tenant_entanglements += 1
            
            # Log cross-tenant entanglement
            if self.audit_logger:
                self.audit_logger.log(
                    "cross_tenant_entanglement",
                    severity="info",
                    details={
                        "vq1": vq1,
                        "vq2": vq2,
                        "tenant1": tenant1,
                        "tenant2": tenant2,
                        "channel_id": channel.channel_id,
                        "gate_type": gate_type
                    }
                )
        
        # Add to graph
        self.graph[vq1].add(vq2)
        self.graph[vq2].add(vq1)
        
        # Create edge metadata
        edge = EntanglementEdge(
            vq1=vq1,
            vq2=vq2,
            tenant1=tenant1,
            tenant2=tenant2,
            channel_id=channel.channel_id if channel else None,
            created_at=time.time(),
            gate_type=gate_type
        )
        
        edge_key = self._edge_key(vq1, vq2)
        self.edges[edge_key] = edge
        
        self.total_entanglements += 1
    
    def is_entangled(self, vq1: str, vq2: str) -> bool:
        """
        Check if two qubits are entangled.
        
        Args:
            vq1: First virtual qubit ID
            vq2: Second virtual qubit ID
        
        Returns:
            True if entangled, False otherwise
        """
        return vq2 in self.graph.get(vq1, set())
    
    def get_entangled_qubits(self, vq_id: str) -> Set[str]:
        """
        Get all qubits entangled with given qubit.
        
        Args:
            vq_id: Virtual qubit ID
        
        Returns:
            Set of entangled qubit IDs
        """
        return self.graph.get(vq_id, set()).copy()
    
    def get_tenant_entanglements(self, tenant_id: str) -> List[EntanglementEdge]:
        """
        Get all entanglements involving a tenant.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            List of EntanglementEdge objects
        """
        result = []
        for edge in self.edges.values():
            if edge.tenant1 == tenant_id or edge.tenant2 == tenant_id:
                result.append(edge)
        return result
    
    def get_cross_tenant_entanglements(self) -> List[EntanglementEdge]:
        """
        Get all cross-tenant entanglements.
        
        Returns:
            List of cross-tenant EntanglementEdge objects
        """
        return [edge for edge in self.edges.values() if edge.is_cross_tenant()]
    
    def create_channel(
        self,
        channel_id: str,
        tenant_a: str,
        tenant_b: str,
        max_entanglements: int = 1000,
        ttl_seconds: Optional[int] = None
    ) -> Channel:
        """
        Create authorized channel for cross-tenant entanglement.
        
        Args:
            channel_id: Unique channel identifier
            tenant_a: First tenant
            tenant_b: Second tenant
            max_entanglements: Maximum entanglements allowed
            ttl_seconds: Time-to-live in seconds (None = no expiration)
        
        Returns:
            Channel object
        """
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        
        channel = Channel(
            channel_id=channel_id,
            tenant_a=tenant_a,
            tenant_b=tenant_b,
            max_entanglements=max_entanglements,
            expires_at=expires_at
        )
        
        self.channels[channel_id] = channel
        
        if self.audit_logger:
            self.audit_logger.log(
                "channel_created",
                severity="info",
                details={
                    "channel_id": channel_id,
                    "tenant_a": tenant_a,
                    "tenant_b": tenant_b,
                    "max_entanglements": max_entanglements,
                    "expires_at": expires_at
                }
            )
        
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """
        Get channel by ID.
        
        Args:
            channel_id: Channel identifier
        
        Returns:
            Channel object or None if not found
        """
        return self.channels.get(channel_id)
    
    def revoke_channel(self, channel_id: str):
        """
        Revoke a channel.
        
        Args:
            channel_id: Channel identifier
        """
        if channel_id in self.channels:
            self.channels[channel_id].is_revoked = True
            self.channels[channel_id].is_active = False
            
            if self.audit_logger:
                self.audit_logger.log(
                    "channel_revoked",
                    severity="warning",
                    details={"channel_id": channel_id}
                )
    
    def cleanup_expired_channels(self) -> int:
        """
        Remove expired channels.
        
        Returns:
            Number of channels removed
        """
        to_remove = [
            cid for cid, channel in self.channels.items()
            if not channel.is_valid()
        ]
        
        for cid in to_remove:
            del self.channels[cid]
        
        return len(to_remove)
    
    def get_statistics(self) -> Dict:
        """
        Get firewall statistics.
        
        Returns:
            Dictionary with statistics
        """
        active_channels = sum(1 for c in self.channels.values() if c.is_valid())
        
        return {
            "total_qubits": len(self.qubit_owners),
            "total_entanglements": self.total_entanglements,
            "cross_tenant_entanglements": self.cross_tenant_entanglements,
            "firewall_violations": self.firewall_violations,
            "active_channels": active_channels,
            "total_channels": len(self.channels),
            "entanglement_edges": len(self.edges)
        }
    
    def verify_invariant(self) -> Tuple[bool, List[str]]:
        """
        Verify firewall invariant: no cross-tenant entanglement without channel.
        
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        for edge in self.edges.values():
            if edge.is_cross_tenant():
                if edge.channel_id is None:
                    violations.append(
                        f"Cross-tenant entanglement without channel: "
                        f"{edge.vq1} ({edge.tenant1}) ↔ {edge.vq2} ({edge.tenant2})"
                    )
                elif edge.channel_id not in self.channels:
                    violations.append(
                        f"Cross-tenant entanglement with unknown channel: "
                        f"{edge.channel_id}"
                    )
                elif not self.channels[edge.channel_id].is_valid():
                    violations.append(
                        f"Cross-tenant entanglement with invalid channel: "
                        f"{edge.channel_id}"
                    )
        
        return len(violations) == 0, violations
    
    def _edge_key(self, vq1: str, vq2: str) -> Tuple[str, str]:
        """Create canonical edge key (sorted)."""
        return tuple(sorted([vq1, vq2]))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "statistics": self.get_statistics(),
            "qubits": dict(self.qubit_owners),
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "channels": {cid: ch.to_dict() for cid, ch in self.channels.items()}
        }
