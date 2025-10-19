"""
Unit tests for Capability Delegator
"""

import unittest
import time
from kernel.security.tenant_manager import TenantManager
from kernel.security.capability_delegator import CapabilityDelegator


class TestCapabilityDelegator(unittest.TestCase):
    """Test capability delegation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tenant_mgr = TenantManager()
        self.delegator = CapabilityDelegator(self.tenant_mgr)
        
        # Create test tenants
        self.tenant_mgr.create_tenant(
            "tenant_1", "Tenant 1",
            capabilities={"CAP_ALLOC", "CAP_TELEPORT"}
        )
        self.tenant_mgr.create_tenant("tenant_2", "Tenant 2")
    
    def test_delegate_capabilities(self):
        """Test delegating capabilities."""
        token = self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"}
        )
        
        self.assertEqual(token.from_tenant, "tenant_1")
        self.assertEqual(token.to_tenant, "tenant_2")
        self.assertIn("CAP_ALLOC", token.capabilities)
        self.assertTrue(token.is_valid())
    
    def test_delegate_without_capability_fails(self):
        """Test that delegating capability you don't have fails."""
        with self.assertRaises(ValueError):
            self.delegator.delegate_capabilities(
                from_tenant="tenant_2",
                to_tenant="tenant_1",
                capabilities={"CAP_ALLOC"}
            )
    
    def test_delegation_with_expiration(self):
        """Test delegation with expiration."""
        token = self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"},
            ttl_seconds=1
        )
        
        self.assertTrue(token.is_valid())
        
        time.sleep(1.1)
        
        self.assertFalse(token.is_valid())
        self.assertTrue(token.is_expired())
    
    def test_revoke_delegation(self):
        """Test revoking a delegation."""
        token = self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"}
        )
        
        self.delegator.revoke_delegation(token.token_id)
        
        self.assertTrue(token.is_revoked)
        self.assertFalse(token.is_valid())
    
    def test_check_delegation(self):
        """Test checking if tenant has delegated capability."""
        self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"}
        )
        
        token = self.delegator.check_delegation("tenant_2", "CAP_ALLOC")
        
        self.assertIsNotNone(token)
        self.assertEqual(token.to_tenant, "tenant_2")
    
    def test_list_delegations(self):
        """Test listing delegations."""
        self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"}
        )
        
        delegations = self.delegator.list_delegations(tenant_id="tenant_1")
        
        self.assertEqual(len(delegations), 1)
        self.assertEqual(delegations[0].from_tenant, "tenant_1")
    
    def test_get_effective_capabilities(self):
        """Test getting effective capabilities."""
        self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC", "CAP_TELEPORT"}
        )
        
        caps = self.delegator.get_effective_capabilities("tenant_2")
        
        self.assertIn("CAP_ALLOC", caps)
        self.assertIn("CAP_TELEPORT", caps)
    
    def test_cleanup_expired_delegations(self):
        """Test cleaning up expired delegations."""
        self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"},
            ttl_seconds=1
        )
        
        time.sleep(1.1)
        
        count = self.delegator.cleanup_expired_delegations()
        
        self.assertEqual(count, 1)
    
    def test_delegation_stats(self):
        """Test getting delegation statistics."""
        token = self.delegator.delegate_capabilities(
            from_tenant="tenant_1",
            to_tenant="tenant_2",
            capabilities={"CAP_ALLOC"}
        )
        
        stats = self.delegator.get_delegation_stats()
        
        self.assertEqual(stats["total_delegations"], 1)
        self.assertEqual(stats["active_delegations"], 1)
        
        self.delegator.revoke_delegation(token.token_id)
        
        stats = self.delegator.get_delegation_stats()
        self.assertEqual(stats["revoked_delegations"], 1)


if __name__ == "__main__":
    unittest.main()
