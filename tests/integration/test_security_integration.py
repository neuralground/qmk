"""
Comprehensive Security Integration Tests

Tests the complete security stack:
- Entanglement Firewall
- Capability System
- Linear Type System

All working together in the executor.
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


class TestFullSecurityStack(unittest.TestCase):
    """Test all security systems working together."""
    
    def setUp(self):
        """Set up complete security stack."""
        # Create security systems
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        # Create capability token with all permissions
        self.token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={
                CapabilityType.CAP_ALLOC,
                CapabilityType.CAP_MEASURE,
                CapabilityType.CAP_LINK
            }
        )
        
        # Create executor with all security systems
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,  # MANDATORY certification
            strict_verification=False  # Allow warnings for now
        )
    
    def test_allocate_measure_with_all_security(self):
        """Test allocate → measure with full security stack."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["vq0"],
                        "produces": ["ev0"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Should execute successfully
        result = self.executor.execute(qvm_graph)
        self.assertEqual(result["status"], "COMPLETED")
        
        # Check linear type system
        stats = self.linear_system.get_statistics()
        self.assertEqual(stats["handles_created"], 1)
        self.assertEqual(stats["handles_consumed"], 1)
        self.assertEqual(stats["linearity_violations"], 0)
    
    def test_double_measurement_blocked_by_linear_types(self):
        """Test that double measurement is blocked by linear types."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["vq0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "MEASURE_X",
                        "vqs": ["vq0"],
                        "produces": ["ev1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Static verifier catches double measurement BEFORE execution
        with self.assertRaises(VerificationError) as cm:
            self.executor.execute(qvm_graph)
        
        # Verification should catch use-after-consume
        self.assertIn("verification", str(cm.exception).lower())
    
    def test_cross_tenant_blocked_by_firewall(self):
        """Test that cross-tenant entanglement is blocked by firewall."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq1"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_b"
                        }
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["vq0", "vq1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Static verifier catches cross-tenant violation BEFORE execution
        with self.assertRaises(VerificationError) as cm:
            self.executor.execute(qvm_graph)
        
        # Verification should catch firewall violation
        self.assertIn("verification", str(cm.exception).lower())
    
    def test_missing_capability_blocked(self):
        """Test that operations without required capabilities are blocked."""
        # Create token without MEASURE capability
        limited_token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={CapabilityType.CAP_ALLOC}  # No CAP_MEASURE!
        )
        
        executor = EnhancedExecutor(
            max_physical_qubits=1000,
            capability_system=self.cap_system,
            capability_token=limited_token,
            require_certification=True,
            strict_verification=False
        )
        
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "MEASURE_Z",
                        "vqs": ["vq0"],
                        "produces": ["ev0"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Should fail on measurement (no CAP_MEASURE) during static verification
        with self.assertRaises(VerificationError) as cm:
            executor.execute(qvm_graph)
        
        # Verification should catch missing capability
        self.assertIn("verification", str(cm.exception).lower())
    
    def test_complete_lifecycle_with_all_security(self):
        """Test complete qubit lifecycle with all security systems."""
        qvm_graph = {
            "program": {
                "nodes": [
                    # Allocate two qubits
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0", "vq1"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    # Apply gates (same tenant)
                    {
                        "id": "n2",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["vq0", "vq1"],
                        "args": {}
                    },
                    # Measure both
                    {
                        "id": "n4",
                        "op": "MEASURE_Z",
                        "vqs": ["vq0"],
                        "produces": ["ev0"],
                        "args": {}
                    },
                    {
                        "id": "n5",
                        "op": "MEASURE_Z",
                        "vqs": ["vq1"],
                        "produces": ["ev1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Should execute successfully
        result = self.executor.execute(qvm_graph)
        self.assertEqual(result["status"], "COMPLETED")
        
        # Check all security systems
        
        # Linear types: 2 created, 2 consumed
        linear_stats = self.linear_system.get_statistics()
        self.assertEqual(linear_stats["handles_created"], 2)
        self.assertEqual(linear_stats["handles_consumed"], 2)
        self.assertEqual(linear_stats["linearity_violations"], 0)
        
        # Firewall: 1 entanglement (CNOT), no violations
        firewall_stats = self.firewall.get_statistics()
        self.assertEqual(firewall_stats["total_entanglements"], 1)
        self.assertEqual(firewall_stats["firewall_violations"], 0)
        
        # Capabilities: checks performed, no violations
        cap_stats = self.cap_system.get_statistics()
        self.assertGreater(cap_stats["capability_checks"], 0)
        self.assertEqual(cap_stats["capability_violations"], 0)


class TestSecurityViolationScenarios(unittest.TestCase):
    """Test various security violation scenarios."""
    
    def setUp(self):
        """Set up security systems."""
        self.firewall = EntanglementGraph()
        self.cap_system = CapabilitySystem()
        self.linear_system = LinearTypeSystem()
        
        self.token = self.cap_system.issue_token(
            tenant_id="tenant_a",
            capabilities={
                CapabilityType.CAP_ALLOC,
                CapabilityType.CAP_MEASURE
            }
        )
        
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            linear_type_system=self.linear_system,
            capability_system=self.cap_system,
            capability_token=self.token,
            require_certification=True,
            strict_verification=False
        )
    
    def test_use_after_free_blocked(self):
        """Test that use-after-free is blocked."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "FREE_LQ",
                        "vqs": ["vq0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Should fail during static verification - use-after-free detected
        with self.assertRaises(VerificationError) as cm:
            self.executor.execute(qvm_graph)
        
        # Static verifier should catch use-after-consume
        self.assertIn("verification", str(cm.exception).lower())


if __name__ == '__main__':
    unittest.main()
