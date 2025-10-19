"""
Cryptographic Capability System

Implements object-capability security with HMAC-SHA256 signed tokens.
Capabilities are unforgeable, transferable, and revocable.

Research Foundation:
- Miller et al. (2003): "Capability Myths Demolished"
- Shapiro et al. (1999): "EROS: A Fast Capability System"
"""

import hmac
import hashlib
import time
import secrets
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class CapabilityType(Enum):
    """Types of capabilities in QMK."""
    CAP_ALLOC = "CAP_ALLOC"          # Allocate logical qubits
    CAP_MEASURE = "CAP_MEASURE"      # Measure qubits
    CAP_LINK = "CAP_LINK"            # Create entanglement channels
    CAP_TELEPORT = "CAP_TELEPORT"    # Teleportation operations
    CAP_MAGIC = "CAP_MAGIC"          # Magic state injection
    CAP_ADMIN = "CAP_ADMIN"          # Administrative operations


# Default capability set for basic operations
DEFAULT_CAPABILITIES = {
    CapabilityType.CAP_ALLOC,
    CapabilityType.CAP_MEASURE,
}


@dataclass
class CapabilityToken:
    """
    Cryptographically signed capability token.
    
    Attributes:
        token_id: Unique token identifier
        tenant_id: Tenant that owns this capability
        capabilities: Set of capabilities granted
        signature: HMAC-SHA256 signature
        issued_at: Issuance timestamp
        expires_at: Optional expiration
        use_count: Number of times used (for use-once semantics)
        max_uses: Maximum uses allowed (None = unlimited)
        is_revoked: Whether token is revoked
        metadata: Additional metadata
    """
    token_id: str
    tenant_id: str
    capabilities: Set[CapabilityType]
    signature: str
    issued_at: float
    expires_at: Optional[float] = None
    use_count: int = 0
    max_uses: Optional[int] = None
    is_revoked: bool = False
    metadata: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if token is valid."""
        if self.is_revoked:
            return False
        
        if self.expires_at and time.time() > self.expires_at:
            return False
        
        if self.max_uses and self.use_count >= self.max_uses:
            return False
        
        return True
    
    def has_capability(self, cap: CapabilityType) -> bool:
        """Check if token has specific capability."""
        return cap in self.capabilities and self.is_valid()
    
    def use(self) -> bool:
        """
        Use the token (increment use count).
        
        Returns:
            True if successful, False if token exhausted
        """
        if not self.is_valid():
            return False
        
        self.use_count += 1
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token_id": self.token_id,
            "tenant_id": self.tenant_id,
            "capabilities": [c.value for c in self.capabilities],
            "signature": self.signature,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "use_count": self.use_count,
            "max_uses": self.max_uses,
            "is_revoked": self.is_revoked,
            "is_valid": self.is_valid()
        }


class CapabilitySystem:
    """
    Manages cryptographic capability tokens.
    
    Provides:
    - Token issuance with HMAC-SHA256 signatures
    - Token verification
    - Capability checking
    - Token revocation
    - Attenuation (subset capabilities)
    """
    
    def __init__(self, secret_key: Optional[bytes] = None, audit_logger=None):
        """
        Initialize capability system.
        
        Args:
            secret_key: Secret key for HMAC (generated if not provided)
            audit_logger: Optional AuditLogger for security events
        """
        self.secret_key = secret_key or secrets.token_bytes(32)
        self.audit_logger = audit_logger
        
        # Token storage: token_id -> CapabilityToken
        self.tokens: Dict[str, CapabilityToken] = {}
        
        # Tenant tokens: tenant_id -> set of token_ids
        self.tenant_tokens: Dict[str, Set[str]] = {}
        
        # Statistics
        self.tokens_issued = 0
        self.tokens_revoked = 0
        self.capability_checks = 0
        self.capability_violations = 0
    
    def issue_token(
        self,
        tenant_id: str,
        capabilities: Set[CapabilityType],
        ttl_seconds: Optional[int] = None,
        max_uses: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> CapabilityToken:
        """
        Issue a new capability token.
        
        Args:
            tenant_id: Tenant receiving the token
            capabilities: Set of capabilities to grant
            ttl_seconds: Time-to-live in seconds (None = no expiration)
            max_uses: Maximum uses (None = unlimited)
            metadata: Optional metadata
        
        Returns:
            Signed CapabilityToken
        """
        # Generate unique token ID
        token_id = f"cap_{self.tokens_issued}_{secrets.token_hex(8)}"
        
        # Calculate expiration
        issued_at = time.time()
        expires_at = issued_at + ttl_seconds if ttl_seconds else None
        
        # Create signature payload
        payload = self._create_signature_payload(
            token_id, tenant_id, capabilities, issued_at, expires_at
        )
        
        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create token
        token = CapabilityToken(
            token_id=token_id,
            tenant_id=tenant_id,
            capabilities=capabilities.copy(),
            signature=signature,
            issued_at=issued_at,
            expires_at=expires_at,
            max_uses=max_uses,
            metadata=metadata or {}
        )
        
        # Store token
        self.tokens[token_id] = token
        
        if tenant_id not in self.tenant_tokens:
            self.tenant_tokens[tenant_id] = set()
        self.tenant_tokens[tenant_id].add(token_id)
        
        self.tokens_issued += 1
        
        # Audit log
        if self.audit_logger:
            self.audit_logger.log(
                "capability_token_issued",
                tenant_id=tenant_id,
                details={
                    "token_id": token_id,
                    "capabilities": [c.value for c in capabilities],
                    "expires_at": expires_at,
                    "max_uses": max_uses
                }
            )
        
        return token
    
    def verify_token(self, token: CapabilityToken) -> bool:
        """
        Verify token signature.
        
        Args:
            token: Token to verify
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Recreate signature payload
        payload = self._create_signature_payload(
            token.token_id,
            token.tenant_id,
            token.capabilities,
            token.issued_at,
            token.expires_at
        )
        
        # Compute expected signature
        expected_signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(token.signature, expected_signature)
    
    def check_capability(
        self,
        token: CapabilityToken,
        capability: CapabilityType,
        use_token: bool = False
    ) -> bool:
        """
        Check if token has capability.
        
        Args:
            token: Capability token
            capability: Capability to check
            use_token: Whether to increment use count
        
        Returns:
            True if token has capability and is valid
        """
        self.capability_checks += 1
        
        # Verify signature
        if not self.verify_token(token):
            self.capability_violations += 1
            
            if self.audit_logger:
                self.audit_logger.log(
                    "capability_violation",
                    severity="critical",
                    tenant_id=token.tenant_id,
                    details={
                        "violation_type": "invalid_signature",
                        "token_id": token.token_id,
                        "capability": capability.value
                    }
                )
            
            return False
        
        # Check validity
        if not token.is_valid():
            self.capability_violations += 1
            
            if self.audit_logger:
                self.audit_logger.log(
                    "capability_violation",
                    severity="warning",
                    tenant_id=token.tenant_id,
                    details={
                        "violation_type": "invalid_token",
                        "token_id": token.token_id,
                        "capability": capability.value,
                        "is_revoked": token.is_revoked,
                        "is_expired": token.expires_at and time.time() > token.expires_at
                    }
                )
            
            return False
        
        # Check capability
        if capability not in token.capabilities:
            self.capability_violations += 1
            
            if self.audit_logger:
                self.audit_logger.log(
                    "capability_violation",
                    severity="warning",
                    tenant_id=token.tenant_id,
                    details={
                        "violation_type": "missing_capability",
                        "token_id": token.token_id,
                        "capability": capability.value,
                        "granted_capabilities": [c.value for c in token.capabilities]
                    }
                )
            
            return False
        
        # Use token if requested
        if use_token:
            if not token.use():
                self.capability_violations += 1
                return False
        
        return True
    
    def attenuate_token(
        self,
        original_token: CapabilityToken,
        subset_capabilities: Set[CapabilityType],
        ttl_seconds: Optional[int] = None,
        max_uses: Optional[int] = None
    ) -> Optional[CapabilityToken]:
        """
        Create attenuated token with subset of capabilities.
        
        Attenuation is a key property of capability systems:
        you can only reduce capabilities, never increase them.
        
        Args:
            original_token: Original token
            subset_capabilities: Subset of original capabilities
            ttl_seconds: Optional shorter TTL
            max_uses: Optional use limit
        
        Returns:
            Attenuated token, or None if invalid
        """
        # Verify original token
        if not self.verify_token(original_token):
            return None
        
        if not original_token.is_valid():
            return None
        
        # Verify subset property
        if not subset_capabilities.issubset(original_token.capabilities):
            if self.audit_logger:
                self.audit_logger.log(
                    "capability_violation",
                    severity="error",
                    tenant_id=original_token.tenant_id,
                    details={
                        "violation_type": "invalid_attenuation",
                        "original_token": original_token.token_id,
                        "requested_caps": [c.value for c in subset_capabilities],
                        "granted_caps": [c.value for c in original_token.capabilities]
                    }
                )
            return None
        
        # Calculate new expiration (must not exceed original)
        if ttl_seconds:
            new_expires = time.time() + ttl_seconds
            if original_token.expires_at:
                new_expires = min(new_expires, original_token.expires_at)
        else:
            new_expires = original_token.expires_at
        
        # Issue attenuated token
        return self.issue_token(
            tenant_id=original_token.tenant_id,
            capabilities=subset_capabilities,
            ttl_seconds=int(new_expires - time.time()) if new_expires else None,
            max_uses=max_uses,
            metadata={
                "attenuated_from": original_token.token_id,
                **original_token.metadata
            }
        )
    
    def revoke_token(self, token_id: str):
        """
        Revoke a capability token.
        
        Args:
            token_id: Token ID to revoke
        """
        if token_id in self.tokens:
            token = self.tokens[token_id]
            token.is_revoked = True
            self.tokens_revoked += 1
            
            if self.audit_logger:
                self.audit_logger.log(
                    "capability_token_revoked",
                    severity="info",
                    tenant_id=token.tenant_id,
                    details={"token_id": token_id}
                )
    
    def get_token(self, token_id: str) -> Optional[CapabilityToken]:
        """Get token by ID."""
        return self.tokens.get(token_id)
    
    def list_tenant_tokens(
        self,
        tenant_id: str,
        valid_only: bool = True
    ) -> List[CapabilityToken]:
        """
        List all tokens for a tenant.
        
        Args:
            tenant_id: Tenant ID
            valid_only: Only return valid tokens
        
        Returns:
            List of CapabilityToken objects
        """
        token_ids = self.tenant_tokens.get(tenant_id, set())
        tokens = [self.tokens[tid] for tid in token_ids if tid in self.tokens]
        
        if valid_only:
            tokens = [t for t in tokens if t.is_valid()]
        
        return tokens
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        to_remove = [
            tid for tid, token in self.tokens.items()
            if token.expires_at and time.time() > token.expires_at
        ]
        
        for tid in to_remove:
            token = self.tokens[tid]
            if token.tenant_id in self.tenant_tokens:
                self.tenant_tokens[token.tenant_id].discard(tid)
            del self.tokens[tid]
        
        return len(to_remove)
    
    def get_statistics(self) -> Dict:
        """
        Get capability system statistics.
        
        Returns:
            Dictionary with statistics
        """
        valid_tokens = sum(1 for t in self.tokens.values() if t.is_valid())
        
        return {
            "tokens_issued": self.tokens_issued,
            "tokens_revoked": self.tokens_revoked,
            "active_tokens": valid_tokens,
            "total_tokens": len(self.tokens),
            "capability_checks": self.capability_checks,
            "capability_violations": self.capability_violations
        }
    
    def _create_signature_payload(
        self,
        token_id: str,
        tenant_id: str,
        capabilities: Set[CapabilityType],
        issued_at: float,
        expires_at: Optional[float]
    ) -> str:
        """Create signature payload for HMAC."""
        caps_str = ",".join(sorted(c.value for c in capabilities))
        expires_str = str(expires_at) if expires_at else "never"
        
        return f"{token_id}|{tenant_id}|{caps_str}|{issued_at}|{expires_str}"


# Helper function for backward compatibility
def has_caps(required: Set[CapabilityType], token: CapabilityToken) -> bool:
    """
    Check if token has all required capabilities.
    
    Args:
        required: Set of required capabilities
        token: Capability token
    
    Returns:
        True if token has all required capabilities
    """
    if not token.is_valid():
        return False
    
    return required.issubset(token.capabilities)
