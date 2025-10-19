"""
Unit tests for Tenant Manager
"""

import unittest
from kernel.security.tenant_manager import TenantManager, TenantQuota


class TestTenantManager(unittest.TestCase):
    """Test tenant management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = TenantManager()
    
    def test_default_tenant_exists(self):
        """Test that default tenant is created."""
        tenant = self.manager.get_tenant("default")
        self.assertEqual(tenant.tenant_id, "default")
        self.assertEqual(tenant.namespace, "default")
        self.assertTrue(tenant.is_active)
    
    def test_create_tenant(self):
        """Test creating a new tenant."""
        tenant = self.manager.create_tenant(
            tenant_id="tenant_1",
            name="Test Tenant",
            capabilities={"CAP_ALLOC"}
        )
        
        self.assertEqual(tenant.tenant_id, "tenant_1")
        self.assertEqual(tenant.name, "Test Tenant")
        self.assertIn("CAP_ALLOC", tenant.capabilities)
        self.assertTrue(tenant.is_active)
    
    def test_create_duplicate_tenant_fails(self):
        """Test that creating duplicate tenant fails."""
        self.manager.create_tenant("tenant_1", "Test")
        
        with self.assertRaises(ValueError):
            self.manager.create_tenant("tenant_1", "Test")
    
    def test_get_tenant_by_namespace(self):
        """Test getting tenant by namespace."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        
        retrieved = self.manager.get_tenant_by_namespace(tenant.namespace)
        self.assertEqual(retrieved.tenant_id, "tenant_1")
    
    def test_grant_capability(self):
        """Test granting capability to tenant."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        
        self.manager.grant_capability("tenant_1", "CAP_TELEPORT")
        
        self.assertIn("CAP_TELEPORT", tenant.capabilities)
    
    def test_revoke_capability(self):
        """Test revoking capability from tenant."""
        tenant = self.manager.create_tenant(
            "tenant_1", "Test",
            capabilities={"CAP_ALLOC", "CAP_TELEPORT"}
        )
        
        self.manager.revoke_capability("tenant_1", "CAP_TELEPORT")
        
        self.assertNotIn("CAP_TELEPORT", tenant.capabilities)
        self.assertIn("CAP_ALLOC", tenant.capabilities)
    
    def test_check_capability(self):
        """Test checking tenant capability."""
        self.manager.create_tenant(
            "tenant_1", "Test",
            capabilities={"CAP_ALLOC"}
        )
        
        self.assertTrue(self.manager.check_capability("tenant_1", "CAP_ALLOC"))
        self.assertFalse(self.manager.check_capability("tenant_1", "CAP_TELEPORT"))
    
    def test_check_quota(self):
        """Test quota checking."""
        quota = TenantQuota(max_sessions=5, max_concurrent_jobs=10)
        tenant = self.manager.create_tenant("tenant_1", "Test", quota=quota)
        
        # Within quota
        self.assertTrue(self.manager.check_quota("tenant_1", "sessions", 3))
        
        # Exceeds quota
        self.assertFalse(self.manager.check_quota("tenant_1", "sessions", 10))
    
    def test_increment_usage(self):
        """Test incrementing resource usage."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        
        self.manager.increment_usage("tenant_1", "sessions", 2)
        self.assertEqual(tenant.active_sessions, 2)
        
        self.manager.increment_usage("tenant_1", "jobs", 5)
        self.assertEqual(tenant.active_jobs, 5)
        self.assertEqual(tenant.total_jobs_run, 5)
    
    def test_decrement_usage(self):
        """Test decrementing resource usage."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        tenant.active_sessions = 5
        tenant.active_jobs = 10
        
        self.manager.decrement_usage("tenant_1", "sessions", 2)
        self.assertEqual(tenant.active_sessions, 3)
        
        self.manager.decrement_usage("tenant_1", "jobs", 3)
        self.assertEqual(tenant.active_jobs, 7)
    
    def test_deactivate_tenant(self):
        """Test deactivating a tenant."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        
        self.manager.deactivate_tenant("tenant_1")
        
        self.assertFalse(tenant.is_active)
    
    def test_activate_tenant(self):
        """Test activating a tenant."""
        tenant = self.manager.create_tenant("tenant_1", "Test")
        tenant.is_active = False
        
        self.manager.activate_tenant("tenant_1")
        
        self.assertTrue(tenant.is_active)
    
    def test_list_tenants(self):
        """Test listing tenants."""
        self.manager.create_tenant("tenant_1", "Test 1")
        self.manager.create_tenant("tenant_2", "Test 2")
        
        tenants = self.manager.list_tenants()
        self.assertGreaterEqual(len(tenants), 3)  # Including default
    
    def test_list_active_tenants_only(self):
        """Test listing only active tenants."""
        self.manager.create_tenant("tenant_1", "Test 1")
        tenant2 = self.manager.create_tenant("tenant_2", "Test 2")
        tenant2.is_active = False
        
        active_tenants = self.manager.list_tenants(active_only=True)
        tenant_ids = [t.tenant_id for t in active_tenants]
        
        self.assertIn("tenant_1", tenant_ids)
        self.assertNotIn("tenant_2", tenant_ids)
    
    def test_get_tenant_stats(self):
        """Test getting tenant statistics."""
        self.manager.create_tenant("tenant_1", "Test 1")
        tenant2 = self.manager.create_tenant("tenant_2", "Test 2")
        tenant2.is_active = False
        
        stats = self.manager.get_tenant_stats()
        
        self.assertGreaterEqual(stats["total_tenants"], 3)
        self.assertGreaterEqual(stats["active_tenants"], 2)
        self.assertGreaterEqual(stats["inactive_tenants"], 1)


if __name__ == "__main__":
    unittest.main()
