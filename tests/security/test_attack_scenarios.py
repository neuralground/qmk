"""
Comprehensive Attack Scenario Testing

Tests the security stack against real-world attack scenarios.
Ensures all security layers work together to prevent attacks.

Attack Categories:
1. Information Leakage Attacks
2. Resource Exhaustion Attacks
3. Privilege Escalation Attacks
4. Quantum-Specific Attacks
5. Timing Attacks
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.executor.enhanced_executor import EnhancedExecutor
from kernel.security.entanglement_firewall import (
    EntanglementGraph,
    EntanglementFirewallViolation
)
from kernel.security.capability_system import (
    CapabilitySystem,
    CapabilityType
)
from kernel.types.linear_types import (
    LinearTypeSystem,
    LinearityViolation
)
from qvm.static_verifier import VerificationError


class TestInformationLeakageAttacks(unittest.TestCase):
    """Test attacks attempting to leak information between tenants."""
    
    def setUp(self):
        """Set up security stack."""
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        self.token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE}
        )
        
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,
            strict_verification=True
        )
    
    def test_attack_bell_pair_information_leakage(self):
        """
        Attack: Create Bell pair, share with victim, measure to learn victim's operations.
        
        Classic quantum attack scenario:
        1. Attacker creates Bell pair (q0, q1)
        2. Attacker shares q1 with victim
        3. Victim performs computation on q1
        4. Attacker measures q0 to learn about victim's operations
        
        Defense: Entanglement firewall blocks cross-tenant entanglement.
        """
        attack_graph = {
            "program": {
                "nodes": [
                    # Attacker allocates Bell pair
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["attacker_q0", "attacker_q1"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    # Create Bell pair
                    {
                        "id": "n2",
                        "op": "APPLY_H",
                        "vqs": ["attacker_q0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["attacker_q0", "attacker_q1"],
                        "args": {}
                    },
                    # Victim allocates qubit
                    {
                        "id": "n4",
                        "op": "ALLOC_LQ",
                        "vqs": ["victim_q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "victim"
                        }
                    },
                    # ATTACK: Try to entangle attacker's q1 with victim's q0
                    {
                        "id": "n5",
                        "op": "APPLY_CNOT",
                        "vqs": ["attacker_q1", "victim_q0"],
                        "args": {}  # No channel!
                    }
                ]
            }
        }
        
        # Attack should be BLOCKED by static verification
        with self.assertRaises(VerificationError) as cm:
            self.executor.execute(attack_graph)
        
        # Verify it was caught as firewall violation
        self.assertIn("verification", str(cm.exception).lower())
    
    def test_attack_measurement_side_channel(self):
        """
        Attack: Measure shared qubit to infer victim's operations.
        
        Defense: Linear types prevent double measurement.
        """
        attack_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    # First measurement
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    # ATTACK: Try to measure again to get more information
                    {
                        "id": "n3",
                        "op": "MEASURE_X",
                        "vqs": ["q0"],
                        "produces": ["ev1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Attack should be BLOCKED by static verification (linearity)
        with self.assertRaises(VerificationError):
            self.executor.execute(attack_graph)


class TestResourceExhaustionAttacks(unittest.TestCase):
    """Test attacks attempting to exhaust system resources."""
    
    def setUp(self):
        """Set up security stack."""
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        self.token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_LINK}
        )
        
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,
            strict_verification=False  # Allow warnings for resource tests
        )
    
    def test_attack_channel_quota_exhaustion(self):
        """
        Attack: Exhaust channel quota to deny service.
        
        Defense: Channel quota enforcement.
        """
        # Create channel with limited quota
        channel = self.firewall.create_channel(
            "ch1",
            "attacker",
            "victim",
            max_entanglements=2
        )
        
        attack_graph = {
            "program": {
                "nodes": [
                    # Allocate qubits
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["a0", "a1", "a2"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["v0", "v1", "v2"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "victim"
                        }
                    },
                    # Use up quota
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["a0", "v0"],
                        "args": {"channel": channel}
                    },
                    {
                        "id": "n4",
                        "op": "APPLY_CNOT",
                        "vqs": ["a1", "v1"],
                        "args": {"channel": channel}
                    },
                    # ATTACK: Try to exceed quota
                    {
                        "id": "n5",
                        "op": "APPLY_CNOT",
                        "vqs": ["a2", "v2"],
                        "args": {"channel": channel}
                    },
                    # Cleanup
                    {
                        "id": "n6",
                        "op": "MEASURE_Z",
                        "vqs": ["a0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    {
                        "id": "n7",
                        "op": "MEASURE_Z",
                        "vqs": ["a1"],
                        "produces": ["ev1"],
                        "args": {}
                    },
                    {
                        "id": "n8",
                        "op": "MEASURE_Z",
                        "vqs": ["a2"],
                        "produces": ["ev2"],
                        "args": {}
                    },
                    {
                        "id": "n9",
                        "op": "MEASURE_Z",
                        "vqs": ["v0"],
                        "produces": ["ev3"],
                        "args": {}
                    },
                    {
                        "id": "n10",
                        "op": "MEASURE_Z",
                        "vqs": ["v1"],
                        "produces": ["ev4"],
                        "args": {}
                    },
                    {
                        "id": "n11",
                        "op": "MEASURE_Z",
                        "vqs": ["v2"],
                        "produces": ["ev5"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Attack should be BLOCKED - either by static verification (resource leaks)
        # or by runtime firewall quota enforcement
        with self.assertRaises((VerificationError, EntanglementFirewallViolation)):
            self.executor.execute(attack_graph)


class TestPrivilegeEscalationAttacks(unittest.TestCase):
    """Test attacks attempting to escalate privileges."""
    
    def setUp(self):
        """Set up security stack."""
        self.cap_system = CapabilitySystem()
    
    def test_attack_capability_forgery(self):
        """
        Attack: Forge capability token to gain unauthorized access.
        
        Defense: HMAC-SHA256 signature verification.
        """
        # Create legitimate token
        token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # ATTACK: Try to add CAP_MEASURE by tampering
        original_caps = token.capabilities.copy()
        token.capabilities.add(CapabilityType.CAP_MEASURE)
        
        # Verification should FAIL (signature doesn't match)
        self.assertFalse(self.cap_system.verify_token(token))
        
        # Restore for next test
        token.capabilities = original_caps
    
    def test_attack_capability_attenuation_bypass(self):
        """
        Attack: Try to increase capabilities through attenuation.
        
        Defense: Attenuation can only reduce capabilities.
        """
        # Create token with limited capabilities
        token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC}
        )
        
        # ATTACK: Try to attenuate to superset (should fail)
        attenuated = self.cap_system.attenuate_token(
            token,
            subset_capabilities={
                CapabilityType.CAP_ALLOC,
                CapabilityType.CAP_MEASURE,  # Not in original!
                CapabilityType.CAP_MAGIC     # Not in original!
            }
        )
        
        # Attack should FAIL
        self.assertIsNone(attenuated)
    
    def test_attack_expired_token_reuse(self):
        """
        Attack: Reuse expired token.
        
        Defense: Token expiration checking.
        """
        import time
        
        # Create token with 1 second TTL
        token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC},
            ttl_seconds=1
        )
        
        # Token should be valid initially
        self.assertTrue(token.is_valid())
        
        # Wait for expiration
        time.sleep(1.1)
        
        # ATTACK: Try to use expired token
        self.assertFalse(token.is_valid())
        self.assertFalse(
            self.cap_system.check_capability(token, CapabilityType.CAP_ALLOC)
        )


class TestQuantumSpecificAttacks(unittest.TestCase):
    """Test quantum-specific attack scenarios."""
    
    def setUp(self):
        """Set up security stack."""
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        self.token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE}
        )
        
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,
            strict_verification=True
        )
    
    def test_attack_no_cloning_violation(self):
        """
        Attack: Try to clone quantum state (violates no-cloning theorem).
        
        Defense: Linear types prevent aliasing.
        """
        # This would require creating two handles for same qubit
        # Linear type system prevents this at allocation time
        
        # Try to allocate same qubit twice
        attack_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    # ATTACK: Try to allocate same qubit again
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    }
                ]
            }
        }
        
        # Attack should be BLOCKED by static verification
        with self.assertRaises(VerificationError):
            self.executor.execute(attack_graph)
    
    def test_attack_use_after_measurement(self):
        """
        Attack: Use qubit after measurement (violates quantum mechanics).
        
        Defense: Linear types enforce consumption on measurement.
        """
        attack_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    # ATTACK: Try to use qubit after measurement
                    {
                        "id": "n3",
                        "op": "APPLY_H",
                        "vqs": ["q0"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Attack should be BLOCKED by static verification
        with self.assertRaises(VerificationError):
            self.executor.execute(attack_graph)


class TestCombinedAttacks(unittest.TestCase):
    """Test sophisticated attacks combining multiple techniques."""
    
    def setUp(self):
        """Set up security stack."""
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        self.token = self.cap_system.issue_token(
            tenant_id="attacker",
            capabilities={CapabilityType.CAP_ALLOC, CapabilityType.CAP_MEASURE, CapabilityType.CAP_LINK}
        )
        
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,
            strict_verification=True
        )
    
    def test_attack_multi_stage_information_leakage(self):
        """
        Sophisticated attack: Multi-stage information leakage attempt.
        
        1. Create entanglement with victim (blocked)
        2. If that fails, try to reuse qubits (blocked)
        3. If that fails, try to measure multiple times (blocked)
        
        Defense: All layers work together to block at each stage.
        """
        # Stage 1: Cross-tenant entanglement
        stage1_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["a0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["v0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "victim"
                        }
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["a0", "v0"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Stage 1 BLOCKED by firewall
        with self.assertRaises(VerificationError):
            self.executor.execute(stage1_graph)
        
        # Stage 2: Double allocation
        stage2_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    }
                ]
            }
        }
        
        # Stage 2 BLOCKED by linearity
        with self.assertRaises(VerificationError):
            self.executor.execute(stage2_graph)
        
        # Stage 3: Double measurement
        stage3_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["q0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "attacker"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "MEASURE_X",
                        "vqs": ["q0"],
                        "produces": ["ev1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Stage 3 BLOCKED by linearity
        with self.assertRaises(VerificationError):
            self.executor.execute(stage3_graph)
        
        # ALL STAGES BLOCKED! ✅


class TestSecurityStatistics(unittest.TestCase):
    """Test that security systems collect proper statistics."""
    
    def test_violation_statistics_collection(self):
        """Test that all violations are properly recorded."""
        firewall = EntanglementGraph()
        cap_system = CapabilitySystem()
        linear_system = LinearTypeSystem()
        
        # Test firewall violations
        firewall.register_qubit("q0", "tenant_a")
        firewall.register_qubit("q1", "tenant_b")
        
        try:
            firewall.add_entanglement("q0", "q1", "CNOT")  # No channel
        except:
            pass
        
        stats = firewall.get_statistics()
        self.assertGreater(stats["firewall_violations"], 0)
        
        # Test capability violations
        token = cap_system.issue_token(
            "tenant_a",
            {CapabilityType.CAP_ALLOC}
        )
        
        # Try to use missing capability
        cap_system.check_capability(token, CapabilityType.CAP_MEASURE)
        
        cap_stats = cap_system.get_statistics()
        self.assertGreater(cap_stats["capability_violations"], 0)
        
        # Test linearity violations
        handle = linear_system.create_handle("VQ", "q0", "tenant_a")
        linear_system.consume_handle(handle.handle_id, "MEASURE_Z")
        
        try:
            linear_system.consume_handle(handle.handle_id, "MEASURE_X")
        except:
            pass
        
        linear_stats = linear_system.get_statistics()
        self.assertGreater(linear_stats["linearity_violations"], 0)


if __name__ == '__main__':
    unittest.main()
