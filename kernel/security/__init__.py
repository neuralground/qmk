"""
Security and Multi-Tenant Support

Implements tenant isolation, handle signing, audit logging, capability delegation,
policy enforcement, and entanglement firewall.
"""

from .tenant_manager import TenantManager, Tenant, TenantQuota
from .handle_signer import HandleSigner, SignedHandle
from .audit_logger import AuditLogger, AuditEvent, AuditEventType, AuditSeverity
from .capability_delegator import CapabilityDelegator, DelegationToken
from .policy_engine import SecurityPolicyEngine, Policy, PolicyAction, PolicyDecision
from .entanglement_firewall import (
    EntanglementGraph,
    Channel,
    EntanglementFirewallViolation,
    FirewallViolationType,
    EntanglementEdge
)
from .capability_system import (
    CapabilitySystem,
    CapabilityToken,
    CapabilityType,
    DEFAULT_CAPABILITIES,
    has_caps
)

__all__ = [
    "TenantManager",
    "Tenant",
    "TenantQuota",
    "HandleSigner",
    "SignedHandle",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "CapabilityDelegator",
    "DelegationToken",
    "SecurityPolicyEngine",
    "Policy",
    "PolicyAction",
    "PolicyDecision",
    "EntanglementGraph",
    "Channel",
    "EntanglementFirewallViolation",
    "FirewallViolationType",
    "EntanglementEdge",
    "CapabilitySystem",
    "CapabilityToken",
    "CapabilityType",
    "DEFAULT_CAPABILITIES",
    "has_caps",
]
