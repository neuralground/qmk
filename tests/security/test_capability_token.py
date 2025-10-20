#!/usr/bin/env python3
"""
Comprehensive tests for cryptographic capability tokens.

Tests cover:
- Token creation and signing
- Signature verification
- Expiration handling
- Use count limits
- Attenuation (capability reduction)
- Delegation chains
- Revocation
- Attack scenarios
- Edge cases
"""

import unittest
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.capability_token import (
    CapabilityToken,
    CapabilityTokenManager,
    CapabilityType
)


class TestCapabilityTokenCreation(unittest.TestCase):
    """Test capability token creation and basic properties."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_create_basic_token(self):
        """Test creating a basic capability token."""
        capabilities = {'CAP_ALLOC', 'CAP_COMPUTE'}
        
        token = CapabilityToken(
            capabilities=capabilities,
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertEqual(token.capabilities, capabilities)
        self.assertEqual(token.metadata.tenant_id, self.tenant_id)
        self.assertIsNotNone(token.token_id)
        self.assertIsNotNone(token.signature)
        self.assertEqual(token.use_count, 0)
        self.assertFalse(token.revoked)
    
    def test_token_has_unique_id(self):
        """Test that each token gets a unique ID."""
        token1 = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        token2 = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertNotEqual(token1.token_id, token2.token_id)
    
    def test_create_token_with_ttl(self):
        """Test creating token with custom TTL."""
        ttl = 7200  # 2 hours
        
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            ttl=ttl
        )
        
        time_remaining = token.time_remaining()
        self.assertGreater(time_remaining, ttl - 1)
        self.assertLess(time_remaining, ttl + 1)
    
    def test_create_token_with_use_limit(self):
        """Test creating token with use limit."""
        max_uses = 10
        
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=max_uses
        )
        
        self.assertEqual(token.max_uses, max_uses)
        self.assertEqual(token.uses_remaining(), max_uses)
    
    def test_create_token_with_session(self):
        """Test creating token with session ID."""
        session_id = 'session_123'
        
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            session_id=session_id
        )
        
        self.assertEqual(token.metadata.session_id, session_id)
    
    def test_create_token_with_purpose(self):
        """Test creating token with purpose."""
        purpose = 'Test quantum computation'
        
        token = CapabilityToken(
            capabilities={'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            purpose=purpose
        )
        
        self.assertEqual(token.metadata.purpose, purpose)
    
    def test_cannot_create_token_with_empty_capabilities(self):
        """Test that creating token with empty capabilities raises error."""
        with self.assertRaises(ValueError):
            CapabilityToken(
                capabilities=set(),
                secret_key=self.secret_key,
                tenant_id=self.tenant_id
            )


class TestCapabilityTokenVerification(unittest.TestCase):
    """Test capability token signature verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertTrue(token.verify(self.secret_key))
    
    def test_verify_fails_with_wrong_key(self):
        """Test that verification fails with wrong secret key."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        wrong_key = b'wrong_secret_key'
        self.assertFalse(token.verify(wrong_key))
    
    def test_verify_fails_for_expired_token(self):
        """Test that verification fails for expired token."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            ttl=0  # Expires immediately
        )
        
        time.sleep(0.1)  # Wait for expiration
        self.assertFalse(token.verify(self.secret_key))
    
    def test_verify_fails_for_revoked_token(self):
        """Test that verification fails for revoked token."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        token.revoke()
        self.assertFalse(token.verify(self.secret_key))
    
    def test_verify_fails_when_use_limit_exceeded(self):
        """Test that verification fails when use limit exceeded."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=2
        )
        
        # Use token twice
        token.increment_use_count()
        token.increment_use_count()
        
        # Should fail verification
        self.assertFalse(token.verify(self.secret_key))


class TestCapabilityTokenAttenuation(unittest.TestCase):
    """Test capability token attenuation (capability reduction)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_attenuate_reduces_capabilities(self):
        """Test that attenuation reduces capabilities."""
        original_caps = {'CAP_ALLOC', 'CAP_COMPUTE', 'CAP_MEASURE'}
        
        token = CapabilityToken(
            capabilities=original_caps,
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        # Attenuate to subset
        attenuated = token.attenuate({'CAP_COMPUTE', 'CAP_MEASURE'})
        
        self.assertEqual(attenuated.capabilities, {'CAP_COMPUTE', 'CAP_MEASURE'})
        self.assertTrue(attenuated.verify(self.secret_key))
    
    def test_attenuate_to_single_capability(self):
        """Test attenuating to single capability."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        attenuated = token.attenuate({'CAP_COMPUTE'})
        
        self.assertEqual(attenuated.capabilities, {'CAP_COMPUTE'})
    
    def test_cannot_attenuate_to_superset(self):
        """Test that attenuation cannot increase capabilities."""
        token = CapabilityToken(
            capabilities={'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        # Try to attenuate to superset (should fail)
        with self.assertRaises(ValueError):
            token.attenuate({'CAP_COMPUTE', 'CAP_MEASURE'})
    
    def test_cannot_attenuate_invalid_token(self):
        """Test that cannot attenuate revoked token."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        token.revoke()
        
        with self.assertRaises(ValueError):
            token.attenuate({'CAP_COMPUTE'})
    
    def test_attenuated_token_tracks_parent(self):
        """Test that attenuated token tracks parent."""
        parent = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        child = parent.attenuate({'CAP_COMPUTE'})
        
        self.assertEqual(child.metadata.parent_token_id, parent.token_id)
        self.assertEqual(child.metadata.delegation_depth, 1)
    
    def test_multiple_attenuation_levels(self):
        """Test multiple levels of attenuation."""
        level0 = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE', 'CAP_MEASURE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        level1 = level0.attenuate({'CAP_COMPUTE', 'CAP_MEASURE'})
        level2 = level1.attenuate({'CAP_MEASURE'})
        
        self.assertEqual(level0.metadata.delegation_depth, 0)
        self.assertEqual(level1.metadata.delegation_depth, 1)
        self.assertEqual(level2.metadata.delegation_depth, 2)
        
        self.assertEqual(level2.capabilities, {'CAP_MEASURE'})


class TestCapabilityTokenDelegation(unittest.TestCase):
    """Test capability token delegation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_delegated_token_creation(self):
        """Test creating delegated token."""
        parent = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        child = CapabilityToken(
            capabilities={'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            parent_token=parent
        )
        
        self.assertEqual(child.metadata.parent_token_id, parent.token_id)
        self.assertEqual(child.metadata.delegation_depth, 1)
    
    def test_cannot_delegate_superset_capabilities(self):
        """Test that delegated token cannot have more capabilities than parent."""
        parent = CapabilityToken(
            capabilities={'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        with self.assertRaises(ValueError):
            CapabilityToken(
                capabilities={'CAP_COMPUTE', 'CAP_MEASURE'},
                secret_key=self.secret_key,
                tenant_id=self.tenant_id,
                parent_token=parent
            )


class TestCapabilityTokenUsage(unittest.TestCase):
    """Test capability token usage tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_increment_use_count(self):
        """Test incrementing use count."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=10
        )
        
        self.assertEqual(token.use_count, 0)
        
        token.increment_use_count()
        self.assertEqual(token.use_count, 1)
        
        token.increment_use_count()
        self.assertEqual(token.use_count, 2)
    
    def test_cannot_exceed_use_limit(self):
        """Test that cannot exceed use limit."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=2
        )
        
        token.increment_use_count()
        token.increment_use_count()
        
        with self.assertRaises(ValueError):
            token.increment_use_count()
    
    def test_uses_remaining(self):
        """Test uses_remaining calculation."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=5
        )
        
        self.assertEqual(token.uses_remaining(), 5)
        
        token.increment_use_count()
        self.assertEqual(token.uses_remaining(), 4)
        
        token.increment_use_count()
        self.assertEqual(token.uses_remaining(), 3)
    
    def test_unlimited_uses(self):
        """Test token with unlimited uses."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=None
        )
        
        self.assertIsNone(token.uses_remaining())
        
        # Should be able to increment many times
        for _ in range(100):
            token.increment_use_count()
        
        self.assertEqual(token.use_count, 100)


class TestCapabilityTokenRevocation(unittest.TestCase):
    """Test capability token revocation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_revoke_token(self):
        """Test revoking a token."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertFalse(token.revoked)
        self.assertTrue(token.verify(self.secret_key))
        
        token.revoke()
        
        self.assertTrue(token.revoked)
        self.assertFalse(token.verify(self.secret_key))
    
    def test_revocation_is_permanent(self):
        """Test that revocation is permanent."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        token.revoke()
        
        # Cannot "un-revoke"
        self.assertTrue(token.revoked)
        self.assertFalse(token.verify(self.secret_key))


class TestCapabilityTokenQueries(unittest.TestCase):
    """Test capability token query methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_has_capability(self):
        """Test has_capability method."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertTrue(token.has_capability('CAP_ALLOC'))
        self.assertTrue(token.has_capability('CAP_COMPUTE'))
        self.assertFalse(token.has_capability('CAP_MEASURE'))
    
    def test_has_all_capabilities(self):
        """Test has_all_capabilities method."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE', 'CAP_MEASURE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        self.assertTrue(token.has_all_capabilities({'CAP_ALLOC'}))
        self.assertTrue(token.has_all_capabilities({'CAP_ALLOC', 'CAP_COMPUTE'}))
        self.assertTrue(token.has_all_capabilities({'CAP_ALLOC', 'CAP_COMPUTE', 'CAP_MEASURE'}))
        self.assertFalse(token.has_all_capabilities({'CAP_ALLOC', 'CAP_TELEPORT'}))
    
    def test_time_remaining(self):
        """Test time_remaining calculation."""
        ttl = 3600
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            ttl=ttl
        )
        
        time_remaining = token.time_remaining()
        self.assertGreater(time_remaining, ttl - 1)
        self.assertLess(time_remaining, ttl + 1)
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=10
        )
        
        data = token.to_dict()
        
        self.assertEqual(data['token_id'], token.token_id)
        self.assertEqual(set(data['capabilities']), token.capabilities)
        self.assertEqual(data['tenant_id'], self.tenant_id)
        self.assertEqual(data['max_uses'], 10)
        self.assertEqual(data['use_count'], 0)
        self.assertFalse(data['revoked'])


class TestCapabilityTokenManager(unittest.TestCase):
    """Test capability token manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.manager = CapabilityTokenManager(self.secret_key)
    
    def test_create_token(self):
        """Test creating token via manager."""
        token = self.manager.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.assertIsNotNone(token)
        self.assertIn(token.token_id, self.manager.active_tokens)
    
    def test_verify_token(self):
        """Test verifying token via manager."""
        token = self.manager.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.assertTrue(self.manager.verify_token(token))
    
    def test_revoke_token(self):
        """Test revoking token via manager."""
        token = self.manager.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.assertTrue(self.manager.verify_token(token))
        
        self.manager.revoke_token(token.token_id)
        
        self.assertFalse(self.manager.verify_token(token))
        self.assertIn(token.token_id, self.manager.revocation_list)
    
    def test_cleanup_expired(self):
        """Test cleaning up expired tokens."""
        # Create token that expires immediately
        token = self.manager.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1',
            ttl=0
        )
        
        time.sleep(0.1)
        
        cleaned = self.manager.cleanup_expired()
        
        self.assertEqual(cleaned, 1)
        self.assertNotIn(token.token_id, self.manager.active_tokens)
    
    def test_get_active_tokens(self):
        """Test getting active tokens."""
        token1 = self.manager.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        token2 = self.manager.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant2'
        )
        
        all_tokens = self.manager.get_active_tokens()
        self.assertEqual(len(all_tokens), 2)
        
        tenant1_tokens = self.manager.get_active_tokens(tenant_id='tenant1')
        self.assertEqual(len(tenant1_tokens), 1)
        self.assertEqual(tenant1_tokens[0].token_id, token1.token_id)


class TestSecurityProperties(unittest.TestCase):
    """Test security properties and attack scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.tenant_id = 'test_tenant'
    
    def test_token_forgery_prevention(self):
        """Test that tokens cannot be forged without secret key."""
        # Create token with one key
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        # Try to verify with different key
        attacker_key = b'attacker_key'
        self.assertFalse(token.verify(attacker_key))
    
    def test_capability_amplification_prevention(self):
        """Test that capabilities cannot be amplified."""
        token = CapabilityToken(
            capabilities={'CAP_COMPUTE'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id
        )
        
        # Cannot attenuate to more capabilities
        with self.assertRaises(ValueError):
            token.attenuate({'CAP_COMPUTE', 'CAP_MEASURE', 'CAP_ALLOC'})
    
    def test_replay_attack_prevention_via_use_limits(self):
        """Test that use limits prevent replay attacks."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            max_uses=1
        )
        
        # First use succeeds
        token.increment_use_count()
        
        # Second use fails
        with self.assertRaises(ValueError):
            token.increment_use_count()
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected."""
        token = CapabilityToken(
            capabilities={'CAP_ALLOC'},
            secret_key=self.secret_key,
            tenant_id=self.tenant_id,
            ttl=0
        )
        
        time.sleep(0.1)
        
        # Expired token fails verification
        self.assertFalse(token.verify(self.secret_key))


if __name__ == '__main__':
    unittest.main()
