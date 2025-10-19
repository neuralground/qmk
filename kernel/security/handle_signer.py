"""
Handle Cryptographic Signing

Provides cryptographic signing and verification for resource handles.
Ensures handles cannot be forged or tampered with.
"""

import hmac
import hashlib
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SignedHandle:
    """
    A cryptographically signed resource handle.
    
    Attributes:
        handle_id: Handle identifier
        handle_type: Type of handle (VQ, CH, EV, etc.)
        tenant_id: Owning tenant
        session_id: Owning session
        created_at: Creation timestamp
        expires_at: Optional expiration timestamp
        signature: Cryptographic signature
        metadata: Additional metadata
    """
    handle_id: str
    handle_type: str
    tenant_id: str
    session_id: str
    created_at: float
    expires_at: Optional[float]
    signature: str
    metadata: Dict
    
    def is_expired(self) -> bool:
        """Check if handle has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "handle_id": self.handle_id,
            "handle_type": self.handle_type,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "signature": self.signature,
            "metadata": self.metadata
        }


class HandleSigner:
    """
    Cryptographic signing for resource handles.
    
    Provides:
    - Handle signing with HMAC-SHA256
    - Signature verification
    - Expiration checking
    - Tamper detection
    """
    
    def __init__(self, secret_key: Optional[bytes] = None):
        """
        Initialize handle signer.
        
        Args:
            secret_key: Secret key for signing (generates random if None)
        """
        if secret_key is None:
            # Generate random key (in production, use secure key management)
            secret_key = hashlib.sha256(str(time.time()).encode()).digest()
        
        self.secret_key = secret_key
        self.signed_handles: Dict[str, SignedHandle] = {}
    
    def sign_handle(
        self,
        handle_id: str,
        handle_type: str,
        tenant_id: str,
        session_id: str,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> SignedHandle:
        """
        Sign a resource handle.
        
        Args:
            handle_id: Handle identifier
            handle_type: Type of handle (VQ, CH, EV, CAP, BND)
            tenant_id: Owning tenant
            session_id: Owning session
            ttl_seconds: Time-to-live in seconds (None = no expiration)
            metadata: Additional metadata
        
        Returns:
            SignedHandle object
        """
        created_at = time.time()
        expires_at = created_at + ttl_seconds if ttl_seconds else None
        
        # Create signature payload
        payload = self._create_payload(
            handle_id, handle_type, tenant_id, session_id,
            created_at, expires_at
        )
        
        # Generate signature
        signature = self._generate_signature(payload)
        
        signed_handle = SignedHandle(
            handle_id=handle_id,
            handle_type=handle_type,
            tenant_id=tenant_id,
            session_id=session_id,
            created_at=created_at,
            expires_at=expires_at,
            signature=signature,
            metadata=metadata or {}
        )
        
        # Store for verification
        self.signed_handles[handle_id] = signed_handle
        
        return signed_handle
    
    def verify_handle(
        self,
        handle_id: str,
        expected_tenant_id: Optional[str] = None,
        expected_session_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a signed handle.
        
        Args:
            handle_id: Handle identifier
            expected_tenant_id: Expected tenant (None = don't check)
            expected_session_id: Expected session (None = don't check)
        
        Returns:
            (is_valid, error_message) tuple
        """
        # Check if handle exists
        if handle_id not in self.signed_handles:
            return False, f"Handle '{handle_id}' not found"
        
        signed_handle = self.signed_handles[handle_id]
        
        # Check expiration
        if signed_handle.is_expired():
            return False, "Handle has expired"
        
        # Verify signature
        payload = self._create_payload(
            signed_handle.handle_id,
            signed_handle.handle_type,
            signed_handle.tenant_id,
            signed_handle.session_id,
            signed_handle.created_at,
            signed_handle.expires_at
        )
        
        expected_signature = self._generate_signature(payload)
        
        if not hmac.compare_digest(signed_handle.signature, expected_signature):
            return False, "Invalid signature (handle may be tampered)"
        
        # Check tenant ownership
        if expected_tenant_id and signed_handle.tenant_id != expected_tenant_id:
            return False, f"Handle belongs to different tenant"
        
        # Check session ownership
        if expected_session_id and signed_handle.session_id != expected_session_id:
            return False, f"Handle belongs to different session"
        
        return True, None
    
    def get_handle(self, handle_id: str) -> SignedHandle:
        """
        Get a signed handle.
        
        Args:
            handle_id: Handle identifier
        
        Returns:
            SignedHandle object
        
        Raises:
            KeyError: If handle not found
        """
        if handle_id not in self.signed_handles:
            raise KeyError(f"Handle '{handle_id}' not found")
        
        return self.signed_handles[handle_id]
    
    def revoke_handle(self, handle_id: str):
        """
        Revoke a handle.
        
        Args:
            handle_id: Handle identifier
        """
        if handle_id in self.signed_handles:
            del self.signed_handles[handle_id]
    
    def revoke_session_handles(self, session_id: str) -> int:
        """
        Revoke all handles for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Number of handles revoked
        """
        to_revoke = [
            hid for hid, handle in self.signed_handles.items()
            if handle.session_id == session_id
        ]
        
        for hid in to_revoke:
            del self.signed_handles[hid]
        
        return len(to_revoke)
    
    def revoke_tenant_handles(self, tenant_id: str) -> int:
        """
        Revoke all handles for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Number of handles revoked
        """
        to_revoke = [
            hid for hid, handle in self.signed_handles.items()
            if handle.tenant_id == tenant_id
        ]
        
        for hid in to_revoke:
            del self.signed_handles[hid]
        
        return len(to_revoke)
    
    def cleanup_expired_handles(self) -> int:
        """
        Remove expired handles.
        
        Returns:
            Number of handles removed
        """
        to_remove = [
            hid for hid, handle in self.signed_handles.items()
            if handle.is_expired()
        ]
        
        for hid in to_remove:
            del self.signed_handles[hid]
        
        return len(to_remove)
    
    def get_handle_stats(self) -> Dict:
        """
        Get statistics about signed handles.
        
        Returns:
            Dictionary with handle statistics
        """
        total = len(self.signed_handles)
        expired = sum(1 for h in self.signed_handles.values() if h.is_expired())
        
        by_type = {}
        for handle in self.signed_handles.values():
            by_type[handle.handle_type] = by_type.get(handle.handle_type, 0) + 1
        
        return {
            "total_handles": total,
            "expired_handles": expired,
            "active_handles": total - expired,
            "by_type": by_type
        }
    
    def _create_payload(
        self,
        handle_id: str,
        handle_type: str,
        tenant_id: str,
        session_id: str,
        created_at: float,
        expires_at: Optional[float]
    ) -> bytes:
        """Create signature payload."""
        payload_str = f"{handle_id}|{handle_type}|{tenant_id}|{session_id}|{created_at}|{expires_at}"
        return payload_str.encode('utf-8')
    
    def _generate_signature(self, payload: bytes) -> str:
        """Generate HMAC-SHA256 signature."""
        h = hmac.new(self.secret_key, payload, hashlib.sha256)
        return h.hexdigest()
