"""
Cryptographic Capability Tokens

Implements object-capability security model with cryptographic tokens.

This module provides unforgeable capability tokens that grant specific
permissions to quantum operations. Tokens are signed with HMAC-SHA256
and include expiration, use limits, and support for attenuation.

Security Properties:
- Unforgeability: Tokens cannot be created without secret key
- Integrity: Tampering is detected via signature verification
- Confidentiality: Capabilities are explicit, not inferred
- Attenuation: Tokens can be restricted but not amplified
- Revocation: Tokens can be invalidated

Example:
    >>> # Create token with basic capabilities
    >>> token = CapabilityToken(
    ...     capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
    ...     secret_key=b'secret',
    ...     tenant_id='tenant1',
    ...     ttl=3600
    ... )
    >>> 
    >>> # Verify token
    >>> if token.verify(b'secret'):
    ...     print("Token is valid")
    >>> 
    >>> # Attenuate token (reduce capabilities)
    >>> limited_token = token.attenuate({'CAP_COMPUTE'})
    >>> assert limited_token.capabilities == {'CAP_COMPUTE'}

Research:
    - Miller, M. S. (2006). "Robust Composition: Towards a Unified 
      Approach to Access Control and Concurrency Control"
    - Mettler, A., et al. (2010). "Joe-E: A Security-Oriented Subset of Java"
    - Shapiro, J. S., et al. (1999). "EROS: A Fast Capability System"
"""

import hmac
import hashlib
import time
import secrets
import json
from typing import Set, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CapabilityType(Enum):
    """Standard capability types for quantum operations."""
    
    # Resource management
    CAP_ALLOC = "CAP_ALLOC"          # Allocate/free logical qubits
    CAP_RESET = "CAP_RESET"          # Reset qubits to |0⟩
    
    # Computation
    CAP_COMPUTE = "CAP_COMPUTE"      # Apply quantum gates
    CAP_MEASURE = "CAP_MEASURE"      # Measure qubits
    
    # Communication
    CAP_LINK = "CAP_LINK"            # Open/close quantum channels
    CAP_SEND = "CAP_SEND"            # Send qubits through channels
    CAP_RECV = "CAP_RECV"            # Receive qubits from channels
    
    # Advanced operations
    CAP_TELEPORT = "CAP_TELEPORT"    # Quantum teleportation
    CAP_MAGIC = "CAP_MAGIC"          # Magic state injection
    
    # Administrative
    CAP_ADMIN = "CAP_ADMIN"          # Administrative operations
    CAP_DELEGATE = "CAP_DELEGATE"    # Delegate capabilities to others
    
    # Debugging
    CAP_DEBUG = "CAP_DEBUG"          # Debug and introspection


@dataclass
class TokenMetadata:
    """Metadata for capability token."""
    
    token_id: str                    # Unique token identifier
    tenant_id: str                   # Tenant that owns this token
    session_id: Optional[str] = None # Session this token belongs to
    parent_token_id: Optional[str] = None  # Parent token (if delegated)
    delegation_depth: int = 0        # Depth in delegation chain
    created_by: Optional[str] = None # User/process that created token
    purpose: Optional[str] = None    # Human-readable purpose
    tags: Dict[str, str] = field(default_factory=dict)  # Custom tags


class CapabilityToken:
    """
    Cryptographic capability token with HMAC-SHA256 signing.
    
    A capability token represents a set of permissions that can be
    exercised to perform quantum operations. Tokens are unforgeable,
    tamper-evident, and support attenuation (reducing permissions).
    
    Attributes:
        capabilities: Set of capability strings
        metadata: Token metadata (tenant, session, etc.)
        issued_at: Unix timestamp when token was created
        expires_at: Unix timestamp when token expires
        max_uses: Maximum number of times token can be used (None = unlimited)
        use_count: Number of times token has been used
        revoked: Whether token has been revoked
        signature: HMAC-SHA256 signature of token
    
    Security Guarantees:
        - Unforgeability: Cannot create valid token without secret key
        - Integrity: Tampering detected via signature verification
        - Attenuation: Can only reduce capabilities, not increase
        - Expiration: Tokens automatically expire after TTL
        - Use limits: Tokens can be limited to N uses
        - Revocation: Tokens can be explicitly revoked
    """
    
    def __init__(
        self,
        capabilities: Set[str],
        secret_key: bytes,
        tenant_id: str,
        session_id: Optional[str] = None,
        ttl: int = 3600,
        max_uses: Optional[int] = None,
        parent_token: Optional['CapabilityToken'] = None,
        purpose: Optional[str] = None
    ):
        """
        Create a new capability token.
        
        Args:
            capabilities: Set of capability strings (e.g., {'CAP_ALLOC', 'CAP_COMPUTE'})
            secret_key: Secret key for HMAC signing (keep secure!)
            tenant_id: ID of tenant that owns this token
            session_id: Optional session ID
            ttl: Time-to-live in seconds (default: 1 hour)
            max_uses: Maximum number of uses (None = unlimited)
            parent_token: Parent token if this is a delegated token
            purpose: Human-readable purpose for this token
        
        Raises:
            ValueError: If capabilities is empty or invalid
            ValueError: If parent_token exists but capabilities not subset
        """
        if not capabilities:
            raise ValueError("Capabilities cannot be empty")
        
        # Validate attenuation if delegated
        if parent_token:
            if not capabilities.issubset(parent_token.capabilities):
                raise ValueError(
                    f"Delegated token capabilities must be subset of parent. "
                    f"Requested: {capabilities}, Parent: {parent_token.capabilities}"
                )
        
        # Generate unique token ID
        self.token_id = secrets.token_hex(16)
        
        # Capabilities
        self.capabilities = capabilities.copy()
        
        # Metadata
        self.metadata = TokenMetadata(
            token_id=self.token_id,
            tenant_id=tenant_id,
            session_id=session_id,
            parent_token_id=parent_token.token_id if parent_token else None,
            delegation_depth=parent_token.metadata.delegation_depth + 1 if parent_token else 0,
            purpose=purpose
        )
        
        # Temporal constraints
        self.issued_at = time.time()
        self.expires_at = self.issued_at + ttl
        
        # Usage constraints
        self.max_uses = max_uses
        self.use_count = 0
        
        # Revocation
        self.revoked = False
        
        # Sign token
        self._secret_key = secret_key
        self.signature = self._sign()
    
    def _sign(self) -> bytes:
        """
        Generate HMAC-SHA256 signature for token.
        
        The signature covers:
        - Token ID
        - Capabilities (sorted for determinism)
        - Tenant ID
        - Session ID
        - Issued timestamp
        - Expiration timestamp
        - Max uses
        - Parent token ID (if delegated)
        
        Returns:
            HMAC-SHA256 signature bytes
        """
        # Build canonical representation
        data = {
            'token_id': self.token_id,
            'capabilities': sorted(list(self.capabilities)),
            'tenant_id': self.metadata.tenant_id,
            'session_id': self.metadata.session_id,
            'issued_at': self.issued_at,
            'expires_at': self.expires_at,
            'max_uses': self.max_uses,
            'parent_token_id': self.metadata.parent_token_id,
            'delegation_depth': self.metadata.delegation_depth
        }
        
        # Serialize to JSON (sorted keys for determinism)
        canonical = json.dumps(data, sort_keys=True).encode('utf-8')
        
        # Compute HMAC-SHA256
        return hmac.new(self._secret_key, canonical, hashlib.sha256).digest()
    
    def verify(self, secret_key: bytes) -> bool:
        """
        Verify token signature and validity.
        
        Checks:
        1. Signature is valid (HMAC-SHA256)
        2. Token has not expired
        3. Token has not been revoked
        4. Token has not exceeded use limit
        
        Args:
            secret_key: Secret key to verify signature
        
        Returns:
            True if token is valid, False otherwise
        
        Security Note:
            Uses constant-time comparison (hmac.compare_digest) to
            prevent timing attacks.
        """
        # Check revocation first (fast path)
        if self.revoked:
            return False
        
        # Check expiration
        if time.time() > self.expires_at:
            return False
        
        # Check use limit
        if self.max_uses is not None and self.use_count >= self.max_uses:
            return False
        
        # Verify signature (constant-time comparison)
        expected_signature = hmac.new(
            secret_key,
            json.dumps({
                'token_id': self.token_id,
                'capabilities': sorted(list(self.capabilities)),
                'tenant_id': self.metadata.tenant_id,
                'session_id': self.metadata.session_id,
                'issued_at': self.issued_at,
                'expires_at': self.expires_at,
                'max_uses': self.max_uses,
                'parent_token_id': self.metadata.parent_token_id,
                'delegation_depth': self.metadata.delegation_depth
            }, sort_keys=True).encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return hmac.compare_digest(self.signature, expected_signature)
    
    def attenuate(self, capabilities: Set[str], **kwargs) -> 'CapabilityToken':
        """
        Create attenuated token with subset of capabilities.
        
        Attenuation is the process of creating a new token with fewer
        capabilities than the original. This is a key security property:
        tokens can be restricted but never amplified.
        
        Args:
            capabilities: Subset of current capabilities
            **kwargs: Additional arguments for new token (ttl, max_uses, etc.)
        
        Returns:
            New attenuated token
        
        Raises:
            ValueError: If requested capabilities not subset of current
            ValueError: If token is revoked or expired
        
        Example:
            >>> token = CapabilityToken({'CAP_ALLOC', 'CAP_COMPUTE'}, ...)
            >>> limited = token.attenuate({'CAP_COMPUTE'})
            >>> assert limited.capabilities == {'CAP_COMPUTE'}
        """
        # Verify token is still valid
        if not self.verify(self._secret_key):
            raise ValueError("Cannot attenuate invalid token")
        
        # Verify attenuation (subset check)
        if not capabilities.issubset(self.capabilities):
            raise ValueError(
                f"Attenuated capabilities must be subset of current. "
                f"Requested: {capabilities}, Current: {self.capabilities}"
            )
        
        # Create new token with reduced capabilities
        return CapabilityToken(
            capabilities=capabilities,
            secret_key=self._secret_key,
            tenant_id=self.metadata.tenant_id,
            session_id=self.metadata.session_id,
            parent_token=self,
            **kwargs
        )
    
    def increment_use_count(self) -> None:
        """
        Increment use count for token.
        
        Should be called after each successful use of the token.
        
        Raises:
            ValueError: If token has reached use limit
        """
        if self.max_uses is not None and self.use_count >= self.max_uses:
            raise ValueError(f"Token has reached use limit ({self.max_uses})")
        
        self.use_count += 1
    
    def revoke(self) -> None:
        """
        Revoke this token.
        
        Once revoked, the token will fail verification and cannot be used.
        Revocation is permanent and cannot be undone.
        
        Note:
            This only revokes the current token. Delegated tokens created
            from this token are NOT automatically revoked (by design).
            Use a revocation list for cascading revocation.
        """
        self.revoked = True
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if token has a specific capability.
        
        Args:
            capability: Capability string to check
        
        Returns:
            True if token has capability, False otherwise
        """
        return capability in self.capabilities
    
    def has_all_capabilities(self, capabilities: Set[str]) -> bool:
        """
        Check if token has all specified capabilities.
        
        Args:
            capabilities: Set of capabilities to check
        
        Returns:
            True if token has all capabilities, False otherwise
        """
        return capabilities.issubset(self.capabilities)
    
    def time_remaining(self) -> float:
        """
        Get remaining time before token expires.
        
        Returns:
            Seconds until expiration (negative if expired)
        """
        return self.expires_at - time.time()
    
    def uses_remaining(self) -> Optional[int]:
        """
        Get remaining uses for token.
        
        Returns:
            Number of uses remaining, or None if unlimited
        """
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.use_count)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize token to dictionary.
        
        Note: Does NOT include secret key or signature for security.
        
        Returns:
            Dictionary representation of token
        """
        return {
            'token_id': self.token_id,
            'capabilities': sorted(list(self.capabilities)),
            'tenant_id': self.metadata.tenant_id,
            'session_id': self.metadata.session_id,
            'issued_at': self.issued_at,
            'expires_at': self.expires_at,
            'max_uses': self.max_uses,
            'use_count': self.use_count,
            'revoked': self.revoked,
            'parent_token_id': self.metadata.parent_token_id,
            'delegation_depth': self.metadata.delegation_depth,
            'purpose': self.metadata.purpose,
            'time_remaining': self.time_remaining(),
            'uses_remaining': self.uses_remaining()
        }
    
    def __repr__(self) -> str:
        """String representation of token."""
        caps = ', '.join(sorted(self.capabilities))
        status = "REVOKED" if self.revoked else "VALID" if self.verify(self._secret_key) else "INVALID"
        return (
            f"CapabilityToken(id={self.token_id[:8]}..., "
            f"caps=[{caps}], "
            f"tenant={self.metadata.tenant_id}, "
            f"status={status})"
        )


class CapabilityTokenManager:
    """
    Manages capability tokens for a QMK instance.
    
    Provides:
    - Token creation with validation
    - Token verification
    - Token revocation
    - Revocation list management
    - Token lifecycle tracking
    """
    
    def __init__(self, secret_key: bytes):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for signing tokens (keep secure!)
        """
        self.secret_key = secret_key
        self.revocation_list: Set[str] = set()  # Revoked token IDs
        self.active_tokens: Dict[str, CapabilityToken] = {}  # Active tokens
    
    def create_token(
        self,
        capabilities: Set[str],
        tenant_id: str,
        **kwargs
    ) -> CapabilityToken:
        """
        Create and register a new capability token.
        
        Args:
            capabilities: Set of capabilities
            tenant_id: Tenant ID
            **kwargs: Additional token parameters
        
        Returns:
            New capability token
        """
        token = CapabilityToken(
            capabilities=capabilities,
            secret_key=self.secret_key,
            tenant_id=tenant_id,
            **kwargs
        )
        
        self.active_tokens[token.token_id] = token
        return token
    
    def verify_token(self, token: CapabilityToken) -> bool:
        """
        Verify token and check revocation list.
        
        Args:
            token: Token to verify
        
        Returns:
            True if valid and not revoked, False otherwise
        """
        # Check revocation list
        if token.token_id in self.revocation_list:
            return False
        
        # Verify token
        return token.verify(self.secret_key)
    
    def revoke_token(self, token_id: str) -> None:
        """
        Revoke a token by ID.
        
        Args:
            token_id: ID of token to revoke
        """
        self.revocation_list.add(token_id)
        
        # Mark token as revoked if we have it
        if token_id in self.active_tokens:
            self.active_tokens[token_id].revoke()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired tokens from active list.
        
        Returns:
            Number of tokens cleaned up
        """
        now = time.time()
        expired = [
            token_id for token_id, token in self.active_tokens.items()
            if token.expires_at < now
        ]
        
        for token_id in expired:
            del self.active_tokens[token_id]
        
        return len(expired)
    
    def get_active_tokens(self, tenant_id: Optional[str] = None) -> list[CapabilityToken]:
        """
        Get list of active tokens.
        
        Args:
            tenant_id: Optional filter by tenant
        
        Returns:
            List of active tokens
        """
        tokens = list(self.active_tokens.values())
        
        if tenant_id:
            tokens = [t for t in tokens if t.metadata.tenant_id == tenant_id]
        
        return tokens
