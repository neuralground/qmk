"""
Tests for Entanglement Firewall

Tests the critical quantum-specific security feature that prevents
unauthorized cross-tenant entanglement.
"""

import unittest
import time
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.entanglement_firewall import (
    EntanglementGraph,
    Channel,
    EntanglementFirewallViolation,
    FirewallViolationType
)


class TestEntanglementGraph(unittest.TestCase):
    """Test EntanglementGraph core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph = EntanglementGraph()
        
        # Register test qubits
        self.graph.register_qubit("vq0", "tenant_a")
        self.graph.register_qubit("vq1", "tenant_a")
        self.graph.register_qubit("vq2", "tenant_b")
        self.graph.register_qubit("vq3", "tenant_b")
    
    def test_qubit_registration(self):
        """Test qubit registration."""
        self.assertEqual(self.graph.qubit_owners["vq0"], "tenant_a")
        self.assertEqual(self.graph.qubit_owners["vq1"], "tenant_a")
        self.assertEqual(self.graph.qubit_owners["vq2"], "tenant_b")
        self.assertEqual(self.graph.qubit_owners["vq3"], "tenant_b")
    
    def test_same_tenant_entanglement_allowed(self):
        """Test that same-tenant entanglement is allowed without channel."""
        # Should succeed - same tenant
        self.graph.add_entanglement("vq0", "vq1", "CNOT")
        
        # Verify entanglement
        self.assertTrue(self.graph.is_entangled("vq0", "vq1"))
        self.assertTrue(self.graph.is_entangled("vq1", "vq0"))
        
        # Check statistics
        stats = self.graph.get_statistics()
        self.assertEqual(stats["total_entanglements"], 1)
        self.assertEqual(stats["cross_tenant_entanglements"], 0)
    
    def test_cross_tenant_without_channel_blocked(self):
        """Test that cross-tenant entanglement without channel is blocked."""
        # Should raise EntanglementFirewallViolation
        with self.assertRaises(EntanglementFirewallViolation) as cm:
            self.graph.add_entanglement("vq0", "vq2", "CNOT")
        
        # Check exception details
        self.assertEqual(
            cm.exception.violation_type,
            FirewallViolationType.MISSING_CHANNEL
        )
        
        # Verify no entanglement created
        self.assertFalse(self.graph.is_entangled("vq0", "vq2"))
        
        # Check violation count
        stats = self.graph.get_statistics()
        self.assertEqual(stats["firewall_violations"], 1)
    
    def test_cross_tenant_with_valid_channel_allowed(self):
        """Test that cross-tenant entanglement with valid channel is allowed."""
        # Create channel
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            max_entanglements=10
        )
        
        # Should succeed with channel
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Verify entanglement
        self.assertTrue(self.graph.is_entangled("vq0", "vq2"))
        
        # Check statistics
        stats = self.graph.get_statistics()
        self.assertEqual(stats["total_entanglements"], 1)
        self.assertEqual(stats["cross_tenant_entanglements"], 1)
        
        # Check channel usage
        self.assertEqual(channel.entanglements_used, 1)
    
    def test_channel_quota_enforcement(self):
        """Test that channel quota is enforced."""
        # Create channel with quota of 2
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            max_entanglements=2
        )
        
        # Register more qubits
        self.graph.register_qubit("vq4", "tenant_a")
        self.graph.register_qubit("vq5", "tenant_b")
        
        # Use up quota
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        self.graph.add_entanglement("vq1", "vq3", "CNOT", channel)
        
        # Third should fail
        with self.assertRaises(EntanglementFirewallViolation) as cm:
            self.graph.add_entanglement("vq4", "vq5", "CNOT", channel)
        
        self.assertEqual(
            cm.exception.violation_type,
            FirewallViolationType.CHANNEL_QUOTA_EXCEEDED
        )
    
    def test_channel_authorization_both_directions(self):
        """Test that channel authorizes both directions."""
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b"
        )
        
        # Should work in both directions
        self.assertTrue(channel.authorizes("tenant_a", "tenant_b"))
        self.assertTrue(channel.authorizes("tenant_b", "tenant_a"))
        
        # Should not authorize other tenants
        self.assertFalse(channel.authorizes("tenant_a", "tenant_c"))
        self.assertFalse(channel.authorizes("tenant_c", "tenant_b"))
    
    def test_channel_expiration(self):
        """Test that expired channels are rejected."""
        # Create channel with 1 second TTL
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            ttl_seconds=1
        )
        
        # Should work initially
        self.assertTrue(channel.is_valid())
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        self.assertFalse(channel.is_valid())
        
        # Should fail with expired channel
        self.graph.register_qubit("vq4", "tenant_a")
        self.graph.register_qubit("vq5", "tenant_b")
        
        with self.assertRaises(EntanglementFirewallViolation):
            self.graph.add_entanglement("vq4", "vq5", "CNOT", channel)
    
    def test_channel_revocation(self):
        """Test that revoked channels are rejected."""
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b"
        )
        
        # Use channel
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Revoke channel
        self.graph.revoke_channel("ch1")
        
        # Should be invalid
        self.assertFalse(channel.is_valid())
        
        # Should fail with revoked channel
        self.graph.register_qubit("vq4", "tenant_a")
        self.graph.register_qubit("vq5", "tenant_b")
        
        with self.assertRaises(EntanglementFirewallViolation):
            self.graph.add_entanglement("vq4", "vq5", "CNOT", channel)
    
    def test_get_entangled_qubits(self):
        """Test getting entangled qubits."""
        # Create entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")
        
        channel = self.graph.create_channel("ch1", "tenant_a", "tenant_b")
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Check vq0's entanglements
        entangled = self.graph.get_entangled_qubits("vq0")
        self.assertEqual(entangled, {"vq1", "vq2"})
        
        # Check vq1's entanglements
        entangled = self.graph.get_entangled_qubits("vq1")
        self.assertEqual(entangled, {"vq0"})
    
    def test_unregister_qubit_removes_entanglements(self):
        """Test that unregistering qubit removes its entanglements."""
        # Create entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")
        
        # Verify entanglement exists
        self.assertTrue(self.graph.is_entangled("vq0", "vq1"))
        
        # Unregister vq0
        self.graph.unregister_qubit("vq0")
        
        # Entanglement should be removed
        self.assertFalse(self.graph.is_entangled("vq0", "vq1"))
        
        # vq1 should have no entanglements
        self.assertEqual(len(self.graph.get_entangled_qubits("vq1")), 0)
    
    def test_get_tenant_entanglements(self):
        """Test getting all entanglements for a tenant."""
        # Create mixed entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")  # tenant_a only
        
        channel = self.graph.create_channel("ch1", "tenant_a", "tenant_b")
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)  # cross-tenant
        
        # Get tenant_a entanglements
        entanglements = self.graph.get_tenant_entanglements("tenant_a")
        self.assertEqual(len(entanglements), 2)
        
        # Get tenant_b entanglements
        entanglements = self.graph.get_tenant_entanglements("tenant_b")
        self.assertEqual(len(entanglements), 1)
    
    def test_get_cross_tenant_entanglements(self):
        """Test getting only cross-tenant entanglements."""
        # Create mixed entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")  # same tenant
        self.graph.add_entanglement("vq2", "vq3", "CNOT")  # same tenant
        
        channel = self.graph.create_channel("ch1", "tenant_a", "tenant_b")
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)  # cross-tenant
        
        # Get cross-tenant only
        cross_tenant = self.graph.get_cross_tenant_entanglements()
        self.assertEqual(len(cross_tenant), 1)
        self.assertTrue(cross_tenant[0].is_cross_tenant())
    
    def test_verify_invariant_valid(self):
        """Test invariant verification with valid state."""
        # Create valid entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")
        
        channel = self.graph.create_channel("ch1", "tenant_a", "tenant_b")
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Verify invariant
        is_valid, violations = self.graph.verify_invariant()
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)
    
    def test_statistics(self):
        """Test statistics collection."""
        # Create entanglements
        self.graph.add_entanglement("vq0", "vq1", "CNOT")
        
        channel = self.graph.create_channel("ch1", "tenant_a", "tenant_b")
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel)
        
        # Get statistics
        stats = self.graph.get_statistics()
        
        self.assertEqual(stats["total_qubits"], 4)
        self.assertEqual(stats["total_entanglements"], 2)
        self.assertEqual(stats["cross_tenant_entanglements"], 1)
        self.assertEqual(stats["firewall_violations"], 0)
        self.assertEqual(stats["active_channels"], 1)
        self.assertEqual(stats["total_channels"], 1)
    
    def test_multiple_channels_between_tenants(self):
        """Test multiple channels between same tenants."""
        # Create two channels
        channel1 = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            max_entanglements=1
        )
        channel2 = self.graph.create_channel(
            "ch2",
            "tenant_a",
            "tenant_b",
            max_entanglements=1
        )
        
        # Use first channel
        self.graph.add_entanglement("vq0", "vq2", "CNOT", channel1)
        
        # First channel exhausted, but second should work
        self.graph.register_qubit("vq4", "tenant_a")
        self.graph.register_qubit("vq5", "tenant_b")
        self.graph.add_entanglement("vq4", "vq5", "CNOT", channel2)
        
        # Both should be used
        self.assertEqual(channel1.entanglements_used, 1)
        self.assertEqual(channel2.entanglements_used, 1)
    
    def test_cleanup_expired_channels(self):
        """Test cleanup of expired channels."""
        # Create channels with different TTLs
        self.graph.create_channel("ch1", "tenant_a", "tenant_b", ttl_seconds=1)
        self.graph.create_channel("ch2", "tenant_a", "tenant_b", ttl_seconds=100)
        
        # Wait for first to expire
        time.sleep(1.1)
        
        # Cleanup
        removed = self.graph.cleanup_expired_channels()
        
        # Should remove 1 channel
        self.assertEqual(removed, 1)
        
        # ch1 should be gone, ch2 should remain
        self.assertIsNone(self.graph.get_channel("ch1"))
        self.assertIsNotNone(self.graph.get_channel("ch2"))


class TestChannel(unittest.TestCase):
    """Test Channel class."""
    
    def test_channel_creation(self):
        """Test channel creation."""
        channel = Channel(
            channel_id="ch1",
            tenant_a="tenant_a",
            tenant_b="tenant_b",
            max_entanglements=100
        )
        
        self.assertEqual(channel.channel_id, "ch1")
        self.assertEqual(channel.tenant_a, "tenant_a")
        self.assertEqual(channel.tenant_b, "tenant_b")
        self.assertEqual(channel.max_entanglements, 100)
        self.assertTrue(channel.is_valid())
    
    def test_channel_use(self):
        """Test channel usage."""
        channel = Channel(
            channel_id="ch1",
            tenant_a="tenant_a",
            tenant_b="tenant_b",
            max_entanglements=2
        )
        
        # Use channel
        self.assertTrue(channel.use())
        self.assertEqual(channel.entanglements_used, 1)
        
        self.assertTrue(channel.use())
        self.assertEqual(channel.entanglements_used, 2)
        
        # Should fail when exhausted
        self.assertFalse(channel.use())
        self.assertEqual(channel.entanglements_used, 2)
    
    def test_channel_to_dict(self):
        """Test channel serialization."""
        channel = Channel(
            channel_id="ch1",
            tenant_a="tenant_a",
            tenant_b="tenant_b"
        )
        
        d = channel.to_dict()
        
        self.assertEqual(d["channel_id"], "ch1")
        self.assertEqual(d["tenant_a"], "tenant_a")
        self.assertEqual(d["tenant_b"], "tenant_b")
        self.assertTrue(d["is_valid"])


class TestAttackScenarios(unittest.TestCase):
    """Test attack scenarios that firewall should prevent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph = EntanglementGraph()
        
        # Attacker (tenant_a)
        self.graph.register_qubit("attacker_q0", "tenant_a")
        self.graph.register_qubit("attacker_q1", "tenant_a")
        
        # Victim (tenant_b)
        self.graph.register_qubit("victim_q0", "tenant_b")
        self.graph.register_qubit("victim_q1", "tenant_b")
    
    def test_attack_direct_entanglement(self):
        """Test that attacker cannot directly entangle with victim."""
        # Attacker tries to entangle with victim
        with self.assertRaises(EntanglementFirewallViolation):
            self.graph.add_entanglement(
                "attacker_q0",
                "victim_q0",
                "CNOT"
            )
        
        # Verify no entanglement created
        self.assertFalse(
            self.graph.is_entangled("attacker_q0", "victim_q0")
        )
        
        # Verify violation logged
        stats = self.graph.get_statistics()
        self.assertEqual(stats["firewall_violations"], 1)
    
    def test_attack_expired_channel(self):
        """Test that attacker cannot use expired channel."""
        # Create channel with short TTL
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            ttl_seconds=1
        )
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Attacker tries to use expired channel
        with self.assertRaises(EntanglementFirewallViolation):
            self.graph.add_entanglement(
                "attacker_q0",
                "victim_q0",
                "CNOT",
                channel
            )
    
    def test_attack_quota_exhaustion(self):
        """Test that attacker cannot exceed channel quota."""
        # Create channel with quota of 1
        channel = self.graph.create_channel(
            "ch1",
            "tenant_a",
            "tenant_b",
            max_entanglements=1
        )
        
        # Use up quota
        self.graph.add_entanglement(
            "attacker_q0",
            "victim_q0",
            "CNOT",
            channel
        )
        
        # Try to exceed quota
        with self.assertRaises(EntanglementFirewallViolation):
            self.graph.add_entanglement(
                "attacker_q1",
                "victim_q1",
                "CNOT",
                channel
            )


if __name__ == '__main__':
    unittest.main()
