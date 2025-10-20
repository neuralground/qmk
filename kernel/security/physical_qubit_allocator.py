"""
Physical Qubit Isolation for Multi-Tenant Systems

Enforces strict isolation of physical qubits between tenants to prevent
cross-tenant interference and information leakage.

In a multi-tenant quantum system, physical qubits must be exclusively
allocated to tenants to prevent:
- Quantum state leakage between tenants
- Crosstalk and decoherence interference
- Side-channel attacks via shared resources
- Resource exhaustion attacks

Security Properties:
- Exclusive Allocation: Each physical qubit belongs to at most one tenant
- No Sharing: Physical qubits are never shared between tenants
- Proper Cleanup: Qubits are reset before reallocation
- Resource Quotas: Tenants cannot exceed their allocation limits
- Audit Trail: All allocations are logged

Example:
    >>> allocator = PhysicalQubitAllocator(total_qubits=100)
    >>> 
    >>> # Allocate qubits for tenant
    >>> qubits = allocator.allocate('tenant1', count=10)
    >>> 
    >>> # Verify access
    >>> if allocator.verify_access('tenant1', qubit_id=5):
    ...     # Tenant can access this qubit
    ...     pass
    >>> 
    >>> # Deallocate when done
    >>> allocator.deallocate('tenant1', qubits)

Research:
    - Murali, P., et al. (2019). "Software Mitigation of Crosstalk on 
      Noisy Intermediate-Scale Quantum Computers"
    - Tannu, S. S., & Qureshi, M. K. (2019). "Not All Qubits Are Created 
      Equal: A Case for Variability-Aware Policies for NISQ-Era Quantum 
      Computers"
    - Paler, A., et al. (2020). "Mapping of Quantum Circuits to NISQ 
      Superconducting Processors"
"""

import time
from typing import Set, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class QubitState(Enum):
    """State of a physical qubit."""
    FREE = "FREE"                  # Available for allocation
    ALLOCATED = "ALLOCATED"        # Allocated to a tenant
    RESETTING = "RESETTING"        # Being reset after deallocation
    MAINTENANCE = "MAINTENANCE"    # Under maintenance/calibration
    FAULTY = "FAULTY"             # Faulty, unavailable


@dataclass
class QubitMetadata:
    """Metadata for a physical qubit."""
    qubit_id: int
    state: QubitState
    tenant_id: Optional[str] = None
    allocated_at: Optional[float] = None
    last_reset_at: Optional[float] = None
    allocation_count: int = 0
    error_rate: float = 0.001  # Default error rate
    
    def is_available(self) -> bool:
        """Check if qubit is available for allocation."""
        return self.state == QubitState.FREE


@dataclass
class TenantQuota:
    """Resource quota for a tenant."""
    tenant_id: str
    max_qubits: int
    allocated_qubits: int = 0
    total_allocations: int = 0
    
    def can_allocate(self, count: int) -> bool:
        """Check if tenant can allocate more qubits."""
        return self.allocated_qubits + count <= self.max_qubits
    
    def remaining_quota(self) -> int:
        """Get remaining quota."""
        return self.max_qubits - self.allocated_qubits


@dataclass
class AllocationRecord:
    """Record of a qubit allocation."""
    tenant_id: str
    qubit_ids: Set[int]
    allocated_at: float
    deallocated_at: Optional[float] = None
    
    def duration(self) -> Optional[float]:
        """Get allocation duration in seconds."""
        if self.deallocated_at:
            return self.deallocated_at - self.allocated_at
        return None


class PhysicalQubitAllocator:
    """
    Manages physical qubit allocation with strict tenant isolation.
    
    Ensures that physical qubits are exclusively allocated to tenants
    and properly isolated to prevent cross-tenant interference.
    
    Security Guarantees:
    - Exclusive allocation: No qubit sharing between tenants
    - Proper cleanup: Qubits reset before reallocation
    - Resource quotas: Tenants cannot exceed limits
    - Audit trail: All allocations logged
    - Fault isolation: Faulty qubits isolated
    
    Attributes:
        total_qubits: Total number of physical qubits
        qubits: Metadata for each physical qubit
        allocations: Current allocations by tenant
        quotas: Resource quotas for tenants
        allocation_history: Historical allocation records
    """
    
    def __init__(
        self,
        total_qubits: int,
        default_quota: Optional[int] = None,
        reset_time: float = 0.1
    ):
        """
        Initialize physical qubit allocator.
        
        Args:
            total_qubits: Total number of physical qubits available
            default_quota: Default quota per tenant (None = unlimited)
            reset_time: Time to reset a qubit (seconds)
        """
        if total_qubits <= 0:
            raise ValueError("total_qubits must be positive")
        
        self.total_qubits = total_qubits
        self.default_quota = default_quota
        self.reset_time = reset_time
        
        # Initialize qubit metadata
        self.qubits: Dict[int, QubitMetadata] = {
            i: QubitMetadata(qubit_id=i, state=QubitState.FREE)
            for i in range(total_qubits)
        }
        
        # Track allocations by tenant
        self.allocations: Dict[str, Set[int]] = {}
        
        # Track quotas by tenant
        self.quotas: Dict[str, TenantQuota] = {}
        
        # Allocation history
        self.allocation_history: List[AllocationRecord] = []
        
        # Statistics
        self.total_allocations = 0
        self.total_deallocations = 0
    
    def allocate(
        self,
        tenant_id: str,
        count: int,
        preferred_qubits: Optional[Set[int]] = None
    ) -> Set[int]:
        """
        Allocate physical qubits for a tenant.
        
        Args:
            tenant_id: ID of tenant requesting allocation
            count: Number of qubits to allocate
            preferred_qubits: Optional set of preferred qubit IDs
        
        Returns:
            Set of allocated qubit IDs
        
        Raises:
            ValueError: If count is invalid
            ResourceError: If insufficient qubits available
            QuotaExceededError: If tenant quota exceeded
        
        Security Note:
            Allocated qubits are exclusively owned by the tenant until
            explicitly deallocated. No other tenant can access them.
        """
        if count <= 0:
            raise ValueError("count must be positive")
        
        # Check quota
        quota = self._get_or_create_quota(tenant_id)
        if not quota.can_allocate(count):
            raise QuotaExceededError(
                f"Tenant {tenant_id} quota exceeded. "
                f"Requested: {count}, Available: {quota.remaining_quota()}"
            )
        
        # Find available qubits
        available = self._get_available_qubits()
        
        if len(available) < count:
            raise ResourceError(
                f"Insufficient physical qubits. "
                f"Requested: {count}, Available: {len(available)}"
            )
        
        # Select qubits (prefer requested qubits if available)
        selected = set()
        
        if preferred_qubits:
            # Try to allocate preferred qubits
            preferred_available = preferred_qubits & available
            selected = set(list(preferred_available)[:count])
        
        # Fill remaining with any available qubits
        if len(selected) < count:
            remaining = available - selected
            selected.update(list(remaining)[:count - len(selected)])
        
        # Allocate qubits
        now = time.time()
        for qubit_id in selected:
            qubit = self.qubits[qubit_id]
            qubit.state = QubitState.ALLOCATED
            qubit.tenant_id = tenant_id
            qubit.allocated_at = now
            qubit.allocation_count += 1
        
        # Update tenant allocations
        if tenant_id not in self.allocations:
            self.allocations[tenant_id] = set()
        self.allocations[tenant_id].update(selected)
        
        # Update quota
        quota.allocated_qubits += count
        quota.total_allocations += 1
        
        # Record allocation
        self.allocation_history.append(AllocationRecord(
            tenant_id=tenant_id,
            qubit_ids=selected.copy(),
            allocated_at=now
        ))
        
        self.total_allocations += 1
        
        return selected
    
    def deallocate(
        self,
        tenant_id: str,
        qubit_ids: Set[int],
        reset: bool = True
    ) -> None:
        """
        Deallocate physical qubits from a tenant.
        
        Args:
            tenant_id: ID of tenant deallocating qubits
            qubit_ids: Set of qubit IDs to deallocate
            reset: Whether to reset qubits (recommended for security)
        
        Raises:
            ValueError: If tenant doesn't own the qubits
        
        Security Note:
            Qubits should be reset before reallocation to prevent
            information leakage to the next tenant.
        """
        # Verify tenant owns these qubits
        tenant_qubits = self.allocations.get(tenant_id, set())
        
        if not qubit_ids.issubset(tenant_qubits):
            invalid = qubit_ids - tenant_qubits
            raise ValueError(
                f"Tenant {tenant_id} does not own qubits: {invalid}"
            )
        
        # Deallocate qubits
        now = time.time()
        for qubit_id in qubit_ids:
            qubit = self.qubits[qubit_id]
            
            if reset:
                # Mark for reset (security best practice)
                qubit.state = QubitState.RESETTING
                qubit.last_reset_at = now
                # In real system, would trigger physical reset
            else:
                # Direct to free (not recommended for security)
                qubit.state = QubitState.FREE
            
            qubit.tenant_id = None
            qubit.allocated_at = None
        
        # Update tenant allocations
        self.allocations[tenant_id] -= qubit_ids
        if not self.allocations[tenant_id]:
            del self.allocations[tenant_id]
        
        # Update quota
        quota = self.quotas[tenant_id]
        quota.allocated_qubits -= len(qubit_ids)
        
        # Update allocation history
        for record in reversed(self.allocation_history):
            if (record.tenant_id == tenant_id and 
                record.qubit_ids == qubit_ids and
                record.deallocated_at is None):
                record.deallocated_at = now
                break
        
        self.total_deallocations += 1
        
        # Complete reset if needed
        if reset:
            self._complete_reset(qubit_ids)
    
    def verify_access(self, tenant_id: str, qubit_id: int) -> bool:
        """
        Verify that a tenant has access to a physical qubit.
        
        Args:
            tenant_id: ID of tenant to check
            qubit_id: Physical qubit ID
        
        Returns:
            True if tenant has access, False otherwise
        
        Security Note:
            This is a critical security check. All operations on physical
            qubits should verify access first.
        """
        if qubit_id not in self.qubits:
            return False
        
        qubit = self.qubits[qubit_id]
        return (qubit.state == QubitState.ALLOCATED and 
                qubit.tenant_id == tenant_id)
    
    def get_tenant_qubits(self, tenant_id: str) -> Set[int]:
        """
        Get all qubits allocated to a tenant.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            Set of allocated qubit IDs
        """
        return self.allocations.get(tenant_id, set()).copy()
    
    def get_available_count(self) -> int:
        """
        Get number of available qubits.
        
        Returns:
            Number of free qubits
        """
        return len(self._get_available_qubits())
    
    def set_quota(self, tenant_id: str, max_qubits: int) -> None:
        """
        Set resource quota for a tenant.
        
        Args:
            tenant_id: Tenant ID
            max_qubits: Maximum qubits tenant can allocate
        """
        if tenant_id in self.quotas:
            quota = self.quotas[tenant_id]
            quota.max_qubits = max_qubits
        else:
            self.quotas[tenant_id] = TenantQuota(
                tenant_id=tenant_id,
                max_qubits=max_qubits
            )
    
    def get_quota(self, tenant_id: str) -> TenantQuota:
        """
        Get quota information for a tenant.
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            Tenant quota information
        """
        return self._get_or_create_quota(tenant_id)
    
    def mark_faulty(self, qubit_id: int) -> None:
        """
        Mark a qubit as faulty.
        
        Args:
            qubit_id: Qubit to mark as faulty
        
        Note:
            Faulty qubits are removed from the available pool until
            repaired or recalibrated.
        """
        if qubit_id in self.qubits:
            qubit = self.qubits[qubit_id]
            
            # If allocated, force deallocate
            if qubit.state == QubitState.ALLOCATED and qubit.tenant_id:
                self.deallocate(qubit.tenant_id, {qubit_id}, reset=False)
            
            qubit.state = QubitState.FAULTY
    
    def mark_maintenance(self, qubit_id: int) -> None:
        """
        Mark a qubit as under maintenance.
        
        Args:
            qubit_id: Qubit to mark for maintenance
        """
        if qubit_id in self.qubits:
            qubit = self.qubits[qubit_id]
            
            # If allocated, force deallocate
            if qubit.state == QubitState.ALLOCATED and qubit.tenant_id:
                self.deallocate(qubit.tenant_id, {qubit_id}, reset=False)
            
            qubit.state = QubitState.MAINTENANCE
    
    def restore_qubit(self, qubit_id: int) -> None:
        """
        Restore a faulty or maintenance qubit to service.
        
        Args:
            qubit_id: Qubit to restore
        """
        if qubit_id in self.qubits:
            qubit = self.qubits[qubit_id]
            if qubit.state in (QubitState.FAULTY, QubitState.MAINTENANCE):
                qubit.state = QubitState.FREE
    
    def get_statistics(self) -> Dict:
        """
        Get allocation statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_qubits': self.total_qubits,
            'free_qubits': len(self._get_available_qubits()),
            'allocated_qubits': sum(len(q) for q in self.allocations.values()),
            'faulty_qubits': sum(1 for q in self.qubits.values() 
                                if q.state == QubitState.FAULTY),
            'maintenance_qubits': sum(1 for q in self.qubits.values() 
                                     if q.state == QubitState.MAINTENANCE),
            'total_allocations': self.total_allocations,
            'total_deallocations': self.total_deallocations,
            'active_tenants': len(self.allocations),
            'utilization': (sum(len(q) for q in self.allocations.values()) / 
                          self.total_qubits * 100)
        }
    
    def _get_available_qubits(self) -> Set[int]:
        """Get set of available qubit IDs."""
        return {
            qid for qid, qubit in self.qubits.items()
            if qubit.is_available()
        }
    
    def _get_or_create_quota(self, tenant_id: str) -> TenantQuota:
        """Get or create quota for tenant."""
        if tenant_id not in self.quotas:
            self.quotas[tenant_id] = TenantQuota(
                tenant_id=tenant_id,
                max_qubits=self.default_quota or self.total_qubits
            )
        return self.quotas[tenant_id]
    
    def _complete_reset(self, qubit_ids: Set[int]) -> None:
        """
        Complete reset of qubits.
        
        In a real system, this would wait for physical reset to complete.
        For simulation, we immediately mark as free.
        """
        # Simulate reset time
        # In real system: time.sleep(self.reset_time)
        
        for qubit_id in qubit_ids:
            if qubit_id in self.qubits:
                qubit = self.qubits[qubit_id]
                if qubit.state == QubitState.RESETTING:
                    qubit.state = QubitState.FREE


class ResourceError(Exception):
    """Exception raised when resources are insufficient."""
    pass


class QuotaExceededError(Exception):
    """Exception raised when tenant quota is exceeded."""
    pass
