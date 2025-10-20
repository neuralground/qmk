"""
Capability Mediation System

Enforces capability-based access control for all quantum operations.

This module implements complete mediation - every operation that accesses
protected resources must pass through capability checks. This is a core
security principle: there should be no way to bypass the security checks.

Security Properties:
- Complete Mediation: All operations checked
- Fail-Safe Defaults: Deny by default
- Least Privilege: Minimum capabilities required
- Audit Logging: All checks logged
- Defense in Depth: Multiple layers of checks

Example:
    >>> mediator = CapabilityMediator(secret_key=b'secret')
    >>> 
    >>> # Create token
    >>> token = mediator.create_token(
    ...     capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
    ...     tenant_id='tenant1'
    ... )
    >>> 
    >>> # Check capability before operation
    >>> if mediator.check_capability(token, 'ALLOC_LQ'):
    ...     # Perform allocation
    ...     pass

Research:
    - Saltzer, J. H., & Schroeder, M. D. (1975). "The Protection of 
      Information in Computer Systems"
    - Miller, M. S., et al. (2003). "Capability Myths Demolished"
    - Shapiro, J. S. (2003). "Vulnerabilities in Synchronous IPC Designs"
"""

import time
from typing import Set, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

from .capability_token import CapabilityToken, CapabilityTokenManager


class OperationType(Enum):
    """Quantum operations that require capability checks."""
    
    # Qubit lifecycle
    ALLOC_LQ = "ALLOC_LQ"              # Allocate logical qubit
    FREE_LQ = "FREE_LQ"                # Free logical qubit
    RESET_LQ = "RESET_LQ"              # Reset qubit to |0⟩
    
    # Measurements (CRITICAL - previously unprotected!)
    MEASURE_Z = "MEASURE_Z"            # Z-basis measurement
    MEASURE_X = "MEASURE_X"            # X-basis measurement
    MEASURE_Y = "MEASURE_Y"            # Y-basis measurement
    MEASURE_BELL = "MEASURE_BELL"      # Bell-basis measurement
    
    # Single-qubit gates
    APPLY_H = "APPLY_H"                # Hadamard gate
    APPLY_X = "APPLY_X"                # Pauli-X gate
    APPLY_Y = "APPLY_Y"                # Pauli-Y gate
    APPLY_Z = "APPLY_Z"                # Pauli-Z gate
    APPLY_S = "APPLY_S"                # S gate (√Z)
    APPLY_T = "APPLY_T"                # T gate (√S)
    APPLY_RZ = "APPLY_RZ"              # RZ rotation
    APPLY_RY = "APPLY_RY"              # RY rotation
    
    # Two-qubit gates
    APPLY_CNOT = "APPLY_CNOT"          # CNOT gate
    APPLY_CZ = "APPLY_CZ"              # CZ gate
    APPLY_SWAP = "APPLY_SWAP"          # SWAP gate
    
    # Quantum channels
    OPEN_CHAN = "OPEN_CHAN"            # Open quantum channel
    CLOSE_CHAN = "CLOSE_CHAN"          # Close quantum channel
    SEND_QUBIT = "SEND_QUBIT"          # Send qubit through channel
    RECV_QUBIT = "RECV_QUBIT"          # Receive qubit from channel
    
    # Advanced operations
    TELEPORT_CNOT = "TELEPORT_CNOT"    # Teleported CNOT
    INJECT_T_STATE = "INJECT_T_STATE"  # Magic state injection
    
    # Administrative
    CREATE_SESSION = "CREATE_SESSION"  # Create new session
    DESTROY_SESSION = "DESTROY_SESSION" # Destroy session
    DELEGATE_CAP = "DELEGATE_CAP"      # Delegate capabilities


# Mapping of operations to required capabilities
CAPABILITY_REQUIREMENTS: Dict[str, Set[str]] = {
    # Qubit lifecycle - requires CAP_ALLOC
    "ALLOC_LQ": {"CAP_ALLOC"},
    "FREE_LQ": {"CAP_ALLOC"},
    "RESET_LQ": {"CAP_RESET"},
    
    # Measurements - requires CAP_MEASURE (CRITICAL!)
    "MEASURE_Z": {"CAP_MEASURE"},
    "MEASURE_X": {"CAP_MEASURE"},
    "MEASURE_Y": {"CAP_MEASURE"},
    "MEASURE_BELL": {"CAP_MEASURE"},
    
    # Single-qubit gates - requires CAP_COMPUTE
    "APPLY_H": {"CAP_COMPUTE"},
    "APPLY_X": {"CAP_COMPUTE"},
    "APPLY_Y": {"CAP_COMPUTE"},
    "APPLY_Z": {"CAP_COMPUTE"},
    "APPLY_S": {"CAP_COMPUTE"},
    "APPLY_T": {"CAP_COMPUTE"},
    "APPLY_RZ": {"CAP_COMPUTE"},
    "APPLY_RY": {"CAP_COMPUTE"},
    
    # Two-qubit gates - requires CAP_COMPUTE
    "APPLY_CNOT": {"CAP_COMPUTE"},
    "APPLY_CZ": {"CAP_COMPUTE"},
    "APPLY_SWAP": {"CAP_COMPUTE"},
    
    # Quantum channels - requires CAP_LINK
    "OPEN_CHAN": {"CAP_LINK"},
    "CLOSE_CHAN": {"CAP_LINK"},
    "SEND_QUBIT": {"CAP_SEND"},
    "RECV_QUBIT": {"CAP_RECV"},
    
    # Advanced operations
    "TELEPORT_CNOT": {"CAP_TELEPORT"},
    "INJECT_T_STATE": {"CAP_MAGIC"},
    
    # Administrative - requires CAP_ADMIN
    "CREATE_SESSION": {"CAP_ADMIN"},
    "DESTROY_SESSION": {"CAP_ADMIN"},
    "DELEGATE_CAP": {"CAP_DELEGATE"},
}


@dataclass
class CapabilityCheckResult:
    """Result of a capability check."""
    
    allowed: bool                      # Whether operation is allowed
    operation: str                     # Operation that was checked
    token_id: str                      # Token that was checked
    required_caps: Set[str]            # Capabilities required
    missing_caps: Set[str]             # Capabilities missing (if denied)
    reason: Optional[str] = None       # Reason for denial
    timestamp: float = None            # When check was performed
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class CapabilityMediator:
    """
    Mediates all access to quantum operations via capability checks.
    
    This is the central enforcement point for capability-based security.
    All operations must pass through check_capability() before execution.
    
    Security Principles:
    - Complete Mediation: No bypass possible
    - Fail-Safe Defaults: Deny unless explicitly allowed
    - Least Privilege: Minimum capabilities required
    - Audit Trail: All checks logged
    - Defense in Depth: Multiple validation layers
    
    Attributes:
        token_manager: Manages capability tokens
        audit_enabled: Whether to log capability checks
        strict_mode: Whether to enforce strict checking
    """
    
    def __init__(
        self,
        secret_key: bytes,
        audit_enabled: bool = True,
        strict_mode: bool = True
    ):
        """
        Initialize capability mediator.
        
        Args:
            secret_key: Secret key for token signing
            audit_enabled: Enable audit logging
            strict_mode: Enable strict capability checking
        """
        self.token_manager = CapabilityTokenManager(secret_key)
        self.audit_enabled = audit_enabled
        self.strict_mode = strict_mode
        
        # Statistics
        self.checks_performed = 0
        self.checks_allowed = 0
        self.checks_denied = 0
        
        # Audit log (in-memory for now)
        self.audit_log: list[CapabilityCheckResult] = []
    
    def check_capability(
        self,
        token: CapabilityToken,
        operation: str,
        **kwargs
    ) -> CapabilityCheckResult:
        """
        Check if token has required capabilities for operation.
        
        This is the core security function. Every protected operation
        must call this before execution.
        
        Args:
            token: Capability token to check
            operation: Operation to perform (e.g., 'MEASURE_Z')
            **kwargs: Additional context for audit logging
        
        Returns:
            CapabilityCheckResult with decision and details
        
        Security Note:
            This function implements complete mediation. There should
            be no way to bypass this check for protected operations.
        
        Example:
            >>> result = mediator.check_capability(token, 'MEASURE_Z')
            >>> if result.allowed:
            ...     # Perform measurement
            ...     pass
            >>> else:
            ...     raise SecurityError(result.reason)
        """
        self.checks_performed += 1
        
        # Get required capabilities for operation
        required_caps = CAPABILITY_REQUIREMENTS.get(operation, set())
        
        # If no capabilities required, allow (but log warning)
        if not required_caps and self.strict_mode:
            result = CapabilityCheckResult(
                allowed=False,
                operation=operation,
                token_id=token.token_id,
                required_caps=set(),
                missing_caps=set(),
                reason=f"Operation '{operation}' not in capability requirements"
            )
            self.checks_denied += 1
            self._audit_check(result, **kwargs)
            return result
        
        # Verify token is valid
        if not self.token_manager.verify_token(token):
            result = CapabilityCheckResult(
                allowed=False,
                operation=operation,
                token_id=token.token_id,
                required_caps=required_caps,
                missing_caps=required_caps,
                reason="Token verification failed (expired, revoked, or invalid)"
            )
            self.checks_denied += 1
            self._audit_check(result, **kwargs)
            return result
        
        # Check if token has required capabilities
        missing_caps = required_caps - token.capabilities
        
        if missing_caps:
            result = CapabilityCheckResult(
                allowed=False,
                operation=operation,
                token_id=token.token_id,
                required_caps=required_caps,
                missing_caps=missing_caps,
                reason=f"Missing capabilities: {missing_caps}"
            )
            self.checks_denied += 1
            self._audit_check(result, **kwargs)
            return result
        
        # All checks passed - allow operation
        result = CapabilityCheckResult(
            allowed=True,
            operation=operation,
            token_id=token.token_id,
            required_caps=required_caps,
            missing_caps=set(),
            reason="Capability check passed"
        )
        self.checks_allowed += 1
        self._audit_check(result, **kwargs)
        
        # Increment token use count
        try:
            token.increment_use_count()
        except ValueError:
            # Token reached use limit - this shouldn't happen since
            # verify_token should have caught it, but handle gracefully
            pass
        
        return result
    
    def require_capability(
        self,
        token: CapabilityToken,
        operation: str,
        **kwargs
    ) -> None:
        """
        Check capability and raise exception if denied.
        
        Convenience method for operations that should fail-fast.
        
        Args:
            token: Capability token to check
            operation: Operation to perform
            **kwargs: Additional context
        
        Raises:
            SecurityError: If capability check fails
        
        Example:
            >>> mediator.require_capability(token, 'MEASURE_Z')
            >>> # If we get here, capability check passed
            >>> result = measure_qubit(qubit)
        """
        result = self.check_capability(token, operation, **kwargs)
        
        if not result.allowed:
            raise SecurityError(
                f"Capability check failed for {operation}: {result.reason}"
            )
    
    def create_token(
        self,
        capabilities: Set[str],
        tenant_id: str,
        **kwargs
    ) -> CapabilityToken:
        """
        Create a new capability token.
        
        Convenience method that delegates to token manager.
        
        Args:
            capabilities: Set of capabilities
            tenant_id: Tenant ID
            **kwargs: Additional token parameters
        
        Returns:
            New capability token
        """
        return self.token_manager.create_token(
            capabilities=capabilities,
            tenant_id=tenant_id,
            **kwargs
        )
    
    def revoke_token(self, token_id: str) -> None:
        """
        Revoke a capability token.
        
        Args:
            token_id: ID of token to revoke
        """
        self.token_manager.revoke_token(token_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get capability check statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'checks_performed': self.checks_performed,
            'checks_allowed': self.checks_allowed,
            'checks_denied': self.checks_denied,
            'allow_rate': (
                self.checks_allowed / self.checks_performed
                if self.checks_performed > 0 else 0
            ),
            'deny_rate': (
                self.checks_denied / self.checks_performed
                if self.checks_performed > 0 else 0
            ),
            'active_tokens': len(self.token_manager.active_tokens),
            'revoked_tokens': len(self.token_manager.revocation_list)
        }
    
    def get_audit_log(
        self,
        limit: Optional[int] = None,
        allowed_only: bool = False,
        denied_only: bool = False
    ) -> list[CapabilityCheckResult]:
        """
        Get audit log of capability checks.
        
        Args:
            limit: Maximum number of entries to return
            allowed_only: Only return allowed checks
            denied_only: Only return denied checks
        
        Returns:
            List of capability check results
        """
        log = self.audit_log
        
        if allowed_only:
            log = [r for r in log if r.allowed]
        elif denied_only:
            log = [r for r in log if not r.allowed]
        
        if limit:
            log = log[-limit:]
        
        return log
    
    def _audit_check(self, result: CapabilityCheckResult, **kwargs) -> None:
        """
        Audit a capability check.
        
        Args:
            result: Check result to audit
            **kwargs: Additional context
        """
        if not self.audit_enabled:
            return
        
        # Add to audit log
        self.audit_log.append(result)
        
        # TODO: Integrate with AuditLogger for persistent storage
        # TODO: Add Merkle tree for tamper-evidence


class SecurityError(Exception):
    """Exception raised when security check fails."""
    pass


def get_required_capabilities(operation: str) -> Set[str]:
    """
    Get required capabilities for an operation.
    
    Args:
        operation: Operation name
    
    Returns:
        Set of required capabilities
    
    Example:
        >>> caps = get_required_capabilities('MEASURE_Z')
        >>> print(caps)
        {'CAP_MEASURE'}
    """
    return CAPABILITY_REQUIREMENTS.get(operation, set()).copy()


def operation_requires_capability(operation: str, capability: str) -> bool:
    """
    Check if operation requires a specific capability.
    
    Args:
        operation: Operation name
        capability: Capability to check
    
    Returns:
        True if operation requires capability
    
    Example:
        >>> operation_requires_capability('MEASURE_Z', 'CAP_MEASURE')
        True
        >>> operation_requires_capability('MEASURE_Z', 'CAP_COMPUTE')
        False
    """
    required = CAPABILITY_REQUIREMENTS.get(operation, set())
    return capability in required
