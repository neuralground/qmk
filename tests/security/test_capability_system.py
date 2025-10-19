"""
Tests for Cryptographic Capability System

Tests the production-grade capability system with HMAC-SHA256 tokens.
"""

import unittest
import time
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.capability_system import (
    CapabilitySystem,
    CapabilityToken,
    CapabilityType,
    DEFAULT_CAPABILITIES
)


class TestCapabilitySystem(unittest.TestCase):
    """Test CapabilitySystem core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cap_system = CapabilitySystem()
    
    def test_issue_token(self):
        """Test token issuance."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE}
        )
        
        self.assertIsNotNone(token)
        self.assertEqual(token.tenant_id, "tenant_a")
        self.assertEqual(len(token.capabilities), 2)
        self.assertIn(CapabilityType.CAP_ALLOC, token.capabilities)
        self.assertIn(CapabilityType.CAP_MEASURE, token.capabilities)
        self.assertTrue(token.is_valid())
    
    def test_token_signature_verification(self):
        """Test that token signatures are verified correctly."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Valid token should verify
        self.assertTrue(self.cap_system.verify_token(token))
        
        # Tampered token should fail
        token.tenant_id = "tenant_b"  # Tamper with tenant
        self.assertFalse(self.cap_system.verify_token(token))
    
    def test_check_capability_valid(self):
        """Test capability checking with valid token."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE}
        )
        
        # Should have granted capabilities
        self.assertTrue(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )
        self.assertTrue(
            self.cap_system.check_capability(token, CapabilityType.CAP_MEASURE)
        )
        
        # Should not have other capabilities
        self.assertFalse(
            self.cap_system.check_capability(token, CapabilityType.CAP_MAGIC)
        )
    
    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        # Create token with 1 second TTL
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC},
            ttl_seconds=1
        )
        
        # Should be valid initially
        self.assertTrue(token.is_valid())
        self.assertTrue(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        self.assertFalse(token.is_valid())
        self.assertFalse(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )
    
    def test_token_revocation(self):
        """Test token revocation."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Should be valid initially
        self.assertTrue(token.is_valid())
        
        # Revoke token
        self.cap_system.revoke_token(token.token_id)
        
        # Should be invalid
        self.assertFalse(token.is_valid())
        self.assertFalse(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )
    
    def test_token_use_count(self):
        """Test use count tracking."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC},
            max_uses=2
        )
        
        # Use token twice
        self.assertTrue(
            self.cap_system.check_capability(
                token, CapabilityType.CAP_ALLOC, use_token=True
            )
        )
        self.assertEqual(token.use_count, 1)
        
        self.assertTrue(
            self.cap_system.check_capability(
                token, CapabilityType.CAP_ALLOC, use_token=True
            )
        )
        self.assertEqual(token.use_count, 2)
        
        # Third use should fail
        self.assertFalse(
            self.cap_system.check_capability(
                token, CapabilityType.CAP_ALLOC, use_token=True
            )
        )
    
    def test_attenuation_valid_subset(self):
        """Test attenuation with valid subset of capabilities."""
        # Create token with multiple capabilities
        original = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={
                CapabilityType.CAP_ALLOC,
                CapabilityType.CAP_MEASURE,
                CapabilityType.CAP_MAGIC
            }
        )
        
        # Attenuate to subset
        attenuated = self.cap_system.attenuate_token(
            original,
            subset_capabilities={CapabilityType.CAP_ALLOC}
        )
        
        self.assertIsNotNone(attenuated)
        self.assertEqual(len(attenuated.capabilities), 1)
        self.assertIn(CapabilityType.CAP_ALLOC, attenuated.capabilities)
        
        # Attenuated token should work for subset
        self.assertTrue(
            self.cap_system.check_capability(
                attenuated, CapabilityType.CAP_ALLOC
            )
        )
        
        # But not for capabilities not in subset
        self.assertFalse(
            self.cap_system.check_capability(
                attenuated, CapabilityType.CAP_MAGIC
            )
        )
    
    def test_attenuation_invalid_superset(self):
        """Test that attenuation cannot increase capabilities."""
        # Create token with limited capabilities
        original = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Try to attenuate to superset (should fail)
        attenuated = self.cap_system.attenuate_token(
            original,
            subset_capabilities={
                CapabilityType.CAP_ALLOC,
                CapabilityType.CAP_MAGIC  # Not in original!
            }
        )
        
        # Should return None (invalid attenuation)
        self.assertIsNone(attenuated)
    
    def test_attenuation_shorter_ttl(self):
        """Test attenuation with shorter TTL."""
        # Create token with 10 second TTL
        original = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC},
            ttl_seconds=10
        )
        
        # Attenuate with 2 second TTL
        attenuated = self.cap_system.attenuate_token(
            original,
            subset_capabilities={CapabilityType.CAP_ALLOC},
            ttl_seconds=2
        )
        
        self.assertIsNotNone(attenuated)
        
        # Attenuated should expire before original
        self.assertLess(attenuated.expires_at, original.expires_at)
    
    def test_list_tenant_tokens(self):
        """Test listing tokens for a tenant."""
        # Issue multiple tokens
        token1 = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        token2 = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_MEASURE}
        )
        token3 = self.cap_system.issue_token(
            tenant_id="tenant_b",
            capabilities={CapabilityType.CAP_MAGIC}
        )
        
        # List tenant_a tokens
        tenant_a_tokens = self.cap_system.list_tenant_tokens("tenant_a")
        self.assertEqual(len(tenant_a_tokens), 2)
        
        # List tenant_b tokens
        tenant_b_tokens = self.cap_system.list_tenant_tokens("tenant_b")
        self.assertEqual(len(tenant_b_tokens), 1)
    
    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Create tokens with different TTLs
        token1 = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC},
            ttl_seconds=1
        )
        token2 = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_MEASURE},
            ttl_seconds=100
        )
        
        # Wait for first to expire
        time.sleep(1.1)
        
        # Cleanup
        removed = self.cap_system.cleanup_expired_tokens()
        
        # Should remove 1 token
        self.assertEqual(removed, 1)
        
        # token1 should be gone
        self.assertIsNone(self.cap_system.get_token(token1.token_id))
        
        # token2 should remain
        self.assertIsNotNone(self.cap_system.get_token(token2.token_id))
    
    def test_statistics(self):
        """Test statistics collection."""
        # Issue tokens
        token1 = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        token2 = self.cap_system.issue_token(
            tenant_id="tenant_b",
            capabilities={CapabilityType.CAP_MEASURE}
        )
        
        # Check capabilities
        self.cap_system.check_capability(token1, CapabilityType.CAP_ALLOC)
        self.cap_system.check_capability(token1, CapabilityType.CAP_MAGIC)  # Violation
        
        # Revoke token
        self.cap_system.revoke_token(token2.token_id)
        
        # Get statistics
        stats = self.cap_system.get_statistics()
        
        self.assertEqual(stats["tokens_issued"], 2)
        self.assertEqual(stats["tokens_revoked"], 1)
        self.assertEqual(stats["active_tokens"], 1)
        self.assertEqual(stats["capability_checks"], 2)
        self.assertEqual(stats["capability_violations"], 1)
    
    def test_default_capabilities(self):
        """Test default capability set."""
        self.assertIn(CapabilityType.CAP_ALLOC, DEFAULT_CAPABILITIES)
        self.assertIn(CapabilityType.CAP_MEASURE, DEFAULT_CAPABILITIES)
    
    def test_token_metadata(self):
        """Test token metadata storage."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC},
            metadata={"purpose": "test", "project": "qmk"}
        )
        
        self.assertEqual(token.metadata["purpose"], "test")
        self.assertEqual(token.metadata["project"], "qmk")
    
    def test_token_serialization(self):
        """Test token to_dict serialization."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE}
        )
        
        d = token.to_dict()
        
        self.assertEqual(d["tenant_id"], "tenant_a")
        self.assertEqual(len(d["capabilities"]), 2)
        self.assertIn("CAP_ALLOC", d["capabilities"])
        self.assertTrue(d["is_valid"])


class TestCapabilityViolations(unittest.TestCase):
    """Test capability violation scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cap_system = CapabilitySystem()
    
    def test_tampered_signature_rejected(self):
        """Test that tampered signatures are rejected."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Tamper with signature
        token.signature = "0" * 64
        
        # Should be rejected
        self.assertFalse(self.cap_system.verify_token(token))
        self.assertFalse(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )
    
    def test_tampered_capabilities_rejected(self):
        """Test that tampered capabilities are rejected."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Tamper with capabilities
        token.capabilities.add(CapabilityType.CAP_MAGIC)
        
        # Signature should not match
        self.assertFalse(self.cap_system.verify_token(token))
    
    def test_missing_capability_violation(self):
        """Test violation when checking missing capability."""
        token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # Check for capability not granted
        result = self.cap_system.check_capability(
            token, CapabilityType.CAP_MAGIC
        )
        
        self.assertFalse(result)
        
        # Should record violation
        stats = self.cap_system.get_statistics()
        self.assertGreater(stats["capability_violations"], 0)


if __name__ == '__main__':
    unittest.main()
