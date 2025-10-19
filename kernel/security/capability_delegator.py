"""
Capability Delegation

Allows tenants to delegate capabilities to other tenants or sessions.
"""

import time
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class DelegationToken:
    """
    Represents a capability delegation.
    
    Attributes:
        token_id: Unique token identifier
        from_tenant: Delegating tenant
        to_tenant: Receiving tenant
        capabilities: Delegated capabilities
        constraints: Optional constraints on delegation
        created_at: Creation timestamp
        expires_at: Optional expiration
        is_revoked: Whether token is revoked
    """
    token_id: str
    from_tenant: str
    to_tenant: str
    capabilities: Set[str]
    constraints: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_revoked: bool = False
    
    def is_expired(self) -> bool:
        """Check if delegation has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if delegation is valid."""
        return not self.is_revoked and not self.is_expired()


class CapabilityDelegator:
    """
    Manages capability delegation between tenants.
    
    Provides:
    - Capability delegation with constraints
    - Token-based delegation
    - Revocation support
    - Delegation chains
    """
    
    def __init__(self, tenant_manager):
        """
        Initialize capability delegator.
        
        Args:
            tenant_manager: TenantManager instance
        """
        self.tenant_manager = tenant_manager
        self.delegations: Dict[str, DelegationToken] = {}
        self.delegation_counter = 0
    
    def delegate_capabilities(
        self,
        from_tenant: str,
        to_tenant: str,
        capabilities: Set[str],
        ttl_seconds: Optional[int] = None,
        constraints: Optional[Dict] = None
    ) -> DelegationToken:
        """
        Delegate capabilities from one tenant to another.
        
        Args:
            from_tenant: Delegating tenant ID
            to_tenant: Receiving tenant ID
            capabilities: Capabilities to delegate
            ttl_seconds: Time-to-live in seconds
            constraints: Optional constraints
        
        Returns:
            DelegationToken
        
        Raises:
            ValueError: If delegation is invalid
        """
        # Validate tenants exist
        from_tenant_obj = self.tenant_manager.get_tenant(from_tenant)
        self.tenant_manager.get_tenant(to_tenant)
        
        # Check that from_tenant has the capabilities
        for cap in capabilities:
            if not self.tenant_manager.check_capability(from_tenant, cap):
                raise ValueError(
                    f"Tenant '{from_tenant}' does not have capability '{cap}'"
                )
        
        # Generate token
        token_id = f"deleg_{self.delegation_counter}"
        self.delegation_counter += 1
        
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        
        token = DelegationToken(
            token_id=token_id,
            from_tenant=from_tenant,
            to_tenant=to_tenant,
            capabilities=capabilities.copy(),
            constraints=constraints or {},
            expires_at=expires_at
        )
        
        self.delegations[token_id] = token
        
        # Grant capabilities to receiving tenant
        for cap in capabilities:
            self.tenant_manager.grant_capability(to_tenant, cap)
        
        return token
    
    def revoke_delegation(self, token_id: str):
        """
        Revoke a delegation.
        
        Args:
            token_id: Delegation token ID
        """
        if token_id not in self.delegations:
            raise KeyError(f"Delegation '{token_id}' not found")
        
        token = self.delegations[token_id]
        token.is_revoked = True
        
        # Revoke capabilities from receiving tenant
        # (Only if not granted through other means)
        for cap in token.capabilities:
            self.tenant_manager.revoke_capability(token.to_tenant, cap)
    
    def check_delegation(
        self,
        tenant_id: str,
        capability: str
    ) -> Optional[DelegationToken]:
        """
        Check if tenant has capability through delegation.
        
        Args:
            tenant_id: Tenant ID
            capability: Capability to check
        
        Returns:
            DelegationToken if found, None otherwise
        """
        for token in self.delegations.values():
            if (token.to_tenant == tenant_id and
                capability in token.capabilities and
                token.is_valid()):
                return token
        
        return None
    
    def list_delegations(
        self,
        tenant_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[DelegationToken]:
        """
        List delegations.
        
        Args:
            tenant_id: Filter by tenant (from or to)
            active_only: Only return active delegations
        
        Returns:
            List of DelegationToken objects
        """
        results = []
        
        for token in self.delegations.values():
            if tenant_id:
                if token.from_tenant != tenant_id and token.to_tenant != tenant_id:
                    continue
            
            if active_only and not token.is_valid():
                continue
            
            results.append(token)
        
        return results
    
    def get_effective_capabilities(self, tenant_id: str) -> Set[str]:
        """
        Get all effective capabilities for a tenant (direct + delegated).
        
        Args:
            tenant_id: Tenant ID
        
        Returns:
            Set of capability strings
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        capabilities = tenant.capabilities.copy()
        
        # Add delegated capabilities
        for token in self.delegations.values():
            if token.to_tenant == tenant_id and token.is_valid():
                capabilities.update(token.capabilities)
        
        return capabilities
    
    def cleanup_expired_delegations(self) -> int:
        """
        Remove expired delegations.
        
        Returns:
            Number of delegations removed
        """
        to_remove = [
            tid for tid, token in self.delegations.items()
            if token.is_expired()
        ]
        
        for tid in to_remove:
            del self.delegations[tid]
        
        return len(to_remove)
    
    def get_delegation_stats(self) -> Dict:
        """
        Get delegation statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.delegations)
        active = sum(1 for t in self.delegations.values() if t.is_valid())
        revoked = sum(1 for t in self.delegations.values() if t.is_revoked)
        expired = sum(1 for t in self.delegations.values() if t.is_expired())
        
        return {
            "total_delegations": total,
            "active_delegations": active,
            "revoked_delegations": revoked,
            "expired_delegations": expired
        }
