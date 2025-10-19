"""
Tenant Namespace Manager

Provides multi-tenant isolation with namespaces, resource limits, and access control.
"""

import time
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
import hashlib


@dataclass
class TenantQuota:
    """Resource quotas for a tenant."""
    max_sessions: int = 10
    max_jobs_per_session: int = 100
    max_logical_qubits: int = 1000
    max_physical_qubits: int = 10000
    max_channels: int = 100
    max_concurrent_jobs: int = 10
    
    # Rate limits
    max_jobs_per_minute: int = 60
    max_api_calls_per_minute: int = 1000


@dataclass
class Tenant:
    """
    Represents a tenant in the system.
    
    Attributes:
        tenant_id: Unique tenant identifier
        name: Human-readable tenant name
        namespace: Isolated namespace for resources
        quota: Resource quotas
        capabilities: Granted capabilities
        created_at: Creation timestamp
        is_active: Whether tenant is active
        metadata: Additional tenant metadata
    """
    tenant_id: str
    name: str
    namespace: str
    quota: TenantQuota
    capabilities: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)
    
    # Usage tracking
    active_sessions: int = 0
    active_jobs: int = 0
    total_jobs_run: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "namespace": self.namespace,
            "quota": {
                "max_sessions": self.quota.max_sessions,
                "max_jobs_per_session": self.quota.max_jobs_per_session,
                "max_logical_qubits": self.quota.max_logical_qubits,
                "max_physical_qubits": self.quota.max_physical_qubits,
                "max_channels": self.quota.max_channels,
                "max_concurrent_jobs": self.quota.max_concurrent_jobs,
            },
            "capabilities": list(self.capabilities),
            "created_at": self.created_at,
            "is_active": self.is_active,
            "usage": {
                "active_sessions": self.active_sessions,
                "active_jobs": self.active_jobs,
                "total_jobs_run": self.total_jobs_run
            }
        }


class TenantManager:
    """
    Manages multi-tenant namespaces and isolation.
    
    Provides:
    - Tenant creation and management
    - Namespace isolation
    - Quota enforcement
    - Resource tracking per tenant
    """
    
    def __init__(self):
        """Initialize tenant manager."""
        self.tenants: Dict[str, Tenant] = {}
        self.namespace_to_tenant: Dict[str, str] = {}
        
        # Create default tenant
        self._create_default_tenant()
    
    def _create_default_tenant(self):
        """Create default tenant for single-tenant mode."""
        default_tenant = Tenant(
            tenant_id="default",
            name="Default Tenant",
            namespace="default",
            quota=TenantQuota(),
            capabilities={"CAP_ALLOC", "CAP_TELEPORT", "CAP_MAGIC", 
                         "CAP_LINK", "CAP_CHECKPOINT", "CAP_DEBUG"}
        )
        self.tenants["default"] = default_tenant
        self.namespace_to_tenant["default"] = "default"
    
    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        quota: Optional[TenantQuota] = None,
        capabilities: Optional[Set[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            name: Human-readable name
            quota: Resource quotas (uses default if None)
            capabilities: Initial capabilities
            metadata: Additional metadata
        
        Returns:
            Created Tenant object
        
        Raises:
            ValueError: If tenant already exists
        """
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant '{tenant_id}' already exists")
        
        # Generate namespace
        namespace = self._generate_namespace(tenant_id)
        
        if namespace in self.namespace_to_tenant:
            raise ValueError(f"Namespace collision for tenant '{tenant_id}'")
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            namespace=namespace,
            quota=quota or TenantQuota(),
            capabilities=capabilities or set(),
            metadata=metadata or {}
        )
        
        self.tenants[tenant_id] = tenant
        self.namespace_to_tenant[namespace] = tenant_id
        
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Tenant:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Tenant object
        
        Raises:
            KeyError: If tenant not found
        """
        if tenant_id not in self.tenants:
            raise KeyError(f"Tenant '{tenant_id}' not found")
        
        return self.tenants[tenant_id]
    
    def get_tenant_by_namespace(self, namespace: str) -> Tenant:
        """
        Get tenant by namespace.
        
        Args:
            namespace: Namespace identifier
        
        Returns:
            Tenant object
        
        Raises:
            KeyError: If namespace not found
        """
        if namespace not in self.namespace_to_tenant:
            raise KeyError(f"Namespace '{namespace}' not found")
        
        tenant_id = self.namespace_to_tenant[namespace]
        return self.tenants[tenant_id]
    
    def update_tenant_quota(self, tenant_id: str, quota: TenantQuota):
        """
        Update tenant quota.
        
        Args:
            tenant_id: Tenant identifier
            quota: New quota
        """
        tenant = self.get_tenant(tenant_id)
        tenant.quota = quota
    
    def grant_capability(self, tenant_id: str, capability: str):
        """
        Grant a capability to a tenant.
        
        Args:
            tenant_id: Tenant identifier
            capability: Capability to grant
        """
        tenant = self.get_tenant(tenant_id)
        tenant.capabilities.add(capability)
    
    def revoke_capability(self, tenant_id: str, capability: str):
        """
        Revoke a capability from a tenant.
        
        Args:
            tenant_id: Tenant identifier
            capability: Capability to revoke
        """
        tenant = self.get_tenant(tenant_id)
        tenant.capabilities.discard(capability)
    
    def check_capability(self, tenant_id: str, capability: str) -> bool:
        """
        Check if tenant has a capability.
        
        Args:
            tenant_id: Tenant identifier
            capability: Capability to check
        
        Returns:
            True if tenant has capability
        """
        tenant = self.get_tenant(tenant_id)
        return capability in tenant.capabilities
    
    def check_quota(self, tenant_id: str, resource_type: str, amount: int = 1) -> bool:
        """
        Check if tenant has quota for resource.
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource (sessions, jobs, qubits, etc.)
            amount: Amount to check
        
        Returns:
            True if within quota
        """
        tenant = self.get_tenant(tenant_id)
        
        if resource_type == "sessions":
            return tenant.active_sessions + amount <= tenant.quota.max_sessions
        elif resource_type == "jobs":
            return tenant.active_jobs + amount <= tenant.quota.max_concurrent_jobs
        elif resource_type == "logical_qubits":
            # Would check actual usage from resource manager
            return amount <= tenant.quota.max_logical_qubits
        elif resource_type == "physical_qubits":
            return amount <= tenant.quota.max_physical_qubits
        elif resource_type == "channels":
            return amount <= tenant.quota.max_channels
        
        return False
    
    def increment_usage(self, tenant_id: str, resource_type: str, amount: int = 1):
        """
        Increment tenant resource usage.
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount to increment
        """
        tenant = self.get_tenant(tenant_id)
        
        if resource_type == "sessions":
            tenant.active_sessions += amount
        elif resource_type == "jobs":
            tenant.active_jobs += amount
            tenant.total_jobs_run += amount
    
    def decrement_usage(self, tenant_id: str, resource_type: str, amount: int = 1):
        """
        Decrement tenant resource usage.
        
        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount to decrement
        """
        tenant = self.get_tenant(tenant_id)
        
        if resource_type == "sessions":
            tenant.active_sessions = max(0, tenant.active_sessions - amount)
        elif resource_type == "jobs":
            tenant.active_jobs = max(0, tenant.active_jobs - amount)
    
    def deactivate_tenant(self, tenant_id: str):
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        tenant = self.get_tenant(tenant_id)
        tenant.is_active = False
    
    def activate_tenant(self, tenant_id: str):
        """
        Activate a tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        tenant = self.get_tenant(tenant_id)
        tenant.is_active = True
    
    def list_tenants(self, active_only: bool = False) -> List[Tenant]:
        """
        List all tenants.
        
        Args:
            active_only: Only return active tenants
        
        Returns:
            List of Tenant objects
        """
        tenants = list(self.tenants.values())
        
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        
        return tenants
    
    def get_tenant_stats(self) -> Dict:
        """
        Get statistics about tenants.
        
        Returns:
            Dictionary with tenant statistics
        """
        total = len(self.tenants)
        active = sum(1 for t in self.tenants.values() if t.is_active)
        
        total_sessions = sum(t.active_sessions for t in self.tenants.values())
        total_jobs = sum(t.active_jobs for t in self.tenants.values())
        total_jobs_run = sum(t.total_jobs_run for t in self.tenants.values())
        
        return {
            "total_tenants": total,
            "active_tenants": active,
            "inactive_tenants": total - active,
            "total_active_sessions": total_sessions,
            "total_active_jobs": total_jobs,
            "total_jobs_run": total_jobs_run
        }
    
    def _generate_namespace(self, tenant_id: str) -> str:
        """
        Generate a unique namespace for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Namespace string
        """
        # Use hash to create deterministic but unique namespace
        hash_obj = hashlib.sha256(tenant_id.encode())
        return f"ns_{hash_obj.hexdigest()[:16]}"
    
    def validate_resource_access(
        self,
        tenant_id: str,
        resource_id: str,
        resource_type: str
    ) -> bool:
        """
        Validate that a tenant can access a resource.
        
        Args:
            tenant_id: Tenant identifier
            resource_id: Resource identifier
            resource_type: Type of resource
        
        Returns:
            True if access is allowed
        """
        tenant = self.get_tenant(tenant_id)
        
        # Check if resource belongs to tenant's namespace
        # Resource IDs should be prefixed with namespace
        expected_prefix = f"{tenant.namespace}:"
        
        return resource_id.startswith(expected_prefix)
