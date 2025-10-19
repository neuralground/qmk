"""
Unit tests for Security Policy Engine
"""

import unittest
from kernel.security.policy_engine import SecurityPolicyEngine, PolicyAction, PolicyDecision


class TestSecurityPolicyEngine(unittest.TestCase):
    """Test security policy engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SecurityPolicyEngine()
    
    def test_add_policy(self):
        """Test adding a policy."""
        policy = self.engine.add_policy(
            name="test_policy",
            description="Test policy",
            action=PolicyAction.DENY,
            conditions={"resource_type": "sensitive"}
        )
        
        self.assertEqual(policy.name, "test_policy")
        self.assertEqual(policy.action, PolicyAction.DENY)
    
    def test_remove_policy(self):
        """Test removing a policy."""
        policy = self.engine.add_policy(
            "test_policy", "Test", PolicyAction.DENY, {}
        )
        
        self.engine.remove_policy(policy.policy_id)
        
        self.assertNotIn(policy.policy_id, self.engine.policies)
    
    def test_evaluate_access_allow(self):
        """Test access evaluation that allows."""
        decision = self.engine.evaluate_access(
            tenant_id="tenant_1",
            resource_type="normal",
            operation="read"
        )
        
        self.assertEqual(decision, PolicyDecision.ALLOW)
    
    def test_evaluate_access_deny(self):
        """Test access evaluation that denies."""
        self.engine.add_policy(
            "deny_writes",
            "Deny all writes",
            PolicyAction.DENY,
            {"operation": "write"},
            priority=100
        )
        
        decision = self.engine.evaluate_access(
            tenant_id="tenant_1",
            resource_type="data",
            operation="write"
        )
        
        self.assertEqual(decision, PolicyDecision.DENY)
    
    def test_policy_priority(self):
        """Test that higher priority policies are evaluated first."""
        # Low priority allow
        self.engine.add_policy(
            "allow_all",
            "Allow all",
            PolicyAction.ALLOW,
            {},
            priority=1
        )
        
        # High priority deny
        self.engine.add_policy(
            "deny_sensitive",
            "Deny sensitive",
            PolicyAction.DENY,
            {"resource_type": "sensitive"},
            priority=100
        )
        
        # Should deny because high priority policy matches
        decision = self.engine.evaluate_access(
            tenant_id="tenant_1",
            resource_type="sensitive",
            operation="read"
        )
        
        self.assertEqual(decision, PolicyDecision.DENY)
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        # First call should succeed
        self.assertTrue(
            self.engine.check_rate_limit("tenant_1", "submit_job", max_per_minute=2)
        )
        
        # Second call should succeed
        self.assertTrue(
            self.engine.check_rate_limit("tenant_1", "submit_job", max_per_minute=2)
        )
        
        # Third call should fail (exceeds limit)
        self.assertFalse(
            self.engine.check_rate_limit("tenant_1", "submit_job", max_per_minute=2)
        )
    
    def test_list_policies(self):
        """Test listing policies."""
        self.engine.add_policy("policy_1", "Test 1", PolicyAction.DENY, {})
        self.engine.add_policy("policy_2", "Test 2", PolicyAction.ALLOW, {})
        
        policies = self.engine.list_policies()
        
        # Should include default policies plus our 2
        self.assertGreaterEqual(len(policies), 2)
    
    def test_list_active_policies_only(self):
        """Test listing only active policies."""
        policy = self.engine.add_policy("policy_1", "Test", PolicyAction.DENY, {})
        policy.is_active = False
        
        active_policies = self.engine.list_policies(active_only=True)
        
        # Should not include inactive policy
        policy_ids = [p.policy_id for p in active_policies]
        self.assertNotIn(policy.policy_id, policy_ids)
    
    def test_get_policy_stats(self):
        """Test getting policy statistics."""
        self.engine.add_policy("policy_1", "Test 1", PolicyAction.DENY, {})
        self.engine.add_policy("policy_2", "Test 2", PolicyAction.ALLOW, {})
        
        stats = self.engine.get_policy_stats()
        
        self.assertGreaterEqual(stats["total_policies"], 2)
        self.assertIn("deny", stats["by_action"])


if __name__ == "__main__":
    unittest.main()
