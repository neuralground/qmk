"""
Security Policy Engine

Enforces security policies across the system.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class PolicyAction(Enum):
    """Policy enforcement actions."""
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"
    RATE_LIMIT = "rate_limit"


class PolicyDecision(Enum):
    """Policy decision outcomes."""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class Policy:
    """
    Represents a security policy.
    
    Attributes:
        policy_id: Unique policy identifier
        name: Policy name
        description: Policy description
        action: Action to take
        conditions: Conditions for policy application
        priority: Policy priority (higher = evaluated first)
        is_active: Whether policy is active
    """
    policy_id: str
    name: str
    description: str
    action: PolicyAction
    conditions: Dict
    priority: int = 0
    is_active: bool = True


class SecurityPolicyEngine:
    """
    Enforces security policies.
    
    Provides:
    - Policy definition and management
    - Policy evaluation
    - Rate limiting
    - Access control decisions
    """
    
    def __init__(self):
        """Initialize policy engine."""
        self.policies: Dict[str, Policy] = {}
        self.policy_counter = 0
        self.rate_limits: Dict[str, List[float]] = {}
        
        # Create default policies
        self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default security policies."""
        # Policy: Deny access to inactive tenants
        self.add_policy(
            name="deny_inactive_tenants",
            description="Deny access to inactive tenants",
            action=PolicyAction.DENY,
            conditions={"tenant_active": False},
            priority=100
        )
        
        # Policy: Audit all capability grants
        self.add_policy(
            name="audit_capability_grants",
            description="Audit all capability grants",
            action=PolicyAction.AUDIT,
            conditions={"operation": "grant_capability"},
            priority=50
        )
    
    def add_policy(
        self,
        name: str,
        description: str,
        action: PolicyAction,
        conditions: Dict,
        priority: int = 0
    ) -> Policy:
        """
        Add a security policy.
        
        Args:
            name: Policy name
            description: Policy description
            action: Action to take
            conditions: Conditions for policy
            priority: Policy priority
        
        Returns:
            Created Policy object
        """
        policy_id = f"policy_{self.policy_counter}"
        self.policy_counter += 1
        
        policy = Policy(
            policy_id=policy_id,
            name=name,
            description=description,
            action=action,
            conditions=conditions,
            priority=priority
        )
        
        self.policies[policy_id] = policy
        
        return policy
    
    def remove_policy(self, policy_id: str):
        """
        Remove a policy.
        
        Args:
            policy_id: Policy identifier
        """
        if policy_id in self.policies:
            del self.policies[policy_id]
    
    def evaluate_access(
        self,
        tenant_id: str,
        resource_type: str,
        operation: str,
        context: Optional[Dict] = None
    ) -> PolicyDecision:
        """
        Evaluate access based on policies.
        
        Args:
            tenant_id: Tenant requesting access
            resource_type: Type of resource
            operation: Operation being performed
            context: Additional context
        
        Returns:
            PolicyDecision (ALLOW or DENY)
        """
        context = context or {}
        context.update({
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "operation": operation
        })
        
        # Get applicable policies sorted by priority
        applicable = self._get_applicable_policies(context)
        
        # Evaluate policies
        for policy in applicable:
            if policy.action == PolicyAction.DENY:
                return PolicyDecision.DENY
            elif policy.action == PolicyAction.RATE_LIMIT:
                if not self._check_rate_limit(tenant_id, operation):
                    return PolicyDecision.DENY
        
        return PolicyDecision.ALLOW
    
    def check_rate_limit(
        self,
        identifier: str,
        operation: str,
        max_per_minute: int = 60
    ) -> bool:
        """
        Check rate limit for an operation.
        
        Args:
            identifier: Identifier (tenant_id, session_id, etc.)
            operation: Operation being performed
            max_per_minute: Maximum operations per minute
        
        Returns:
            True if within rate limit
        """
        import time
        
        key = f"{identifier}:{operation}"
        current_time = time.time()
        
        # Initialize if not exists
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Remove old entries (older than 1 minute)
        self.rate_limits[key] = [
            t for t in self.rate_limits[key]
            if current_time - t < 60
        ]
        
        # Check limit
        if len(self.rate_limits[key]) >= max_per_minute:
            return False
        
        # Record this operation
        self.rate_limits[key].append(current_time)
        
        return True
    
    def _check_rate_limit(self, tenant_id: str, operation: str) -> bool:
        """Internal rate limit check."""
        return self.check_rate_limit(tenant_id, operation)
    
    def _get_applicable_policies(self, context: Dict) -> List[Policy]:
        """
        Get policies applicable to context.
        
        Args:
            context: Context dictionary
        
        Returns:
            List of applicable policies sorted by priority
        """
        applicable = []
        
        for policy in self.policies.values():
            if not policy.is_active:
                continue
            
            # Check if all conditions match
            if self._matches_conditions(policy.conditions, context):
                applicable.append(policy)
        
        # Sort by priority (highest first)
        applicable.sort(key=lambda p: p.priority, reverse=True)
        
        return applicable
    
    def _matches_conditions(self, conditions: Dict, context: Dict) -> bool:
        """
        Check if context matches policy conditions.
        
        Args:
            conditions: Policy conditions
            context: Context to check
        
        Returns:
            True if all conditions match
        """
        for key, value in conditions.items():
            if key not in context:
                return False
            
            if context[key] != value:
                return False
        
        return True
    
    def get_policy_stats(self) -> Dict:
        """
        Get policy statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.policies)
        active = sum(1 for p in self.policies.values() if p.is_active)
        
        by_action = {}
        for policy in self.policies.values():
            action = policy.action.value
            by_action[action] = by_action.get(action, 0) + 1
        
        return {
            "total_policies": total,
            "active_policies": active,
            "inactive_policies": total - active,
            "by_action": by_action
        }
    
    def list_policies(self, active_only: bool = False) -> List[Policy]:
        """
        List all policies.
        
        Args:
            active_only: Only return active policies
        
        Returns:
            List of Policy objects
        """
        policies = list(self.policies.values())
        
        if active_only:
            policies = [p for p in policies if p.is_active]
        
        # Sort by priority
        policies.sort(key=lambda p: p.priority, reverse=True)
        
        return policies
