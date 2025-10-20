"""
Integration Tests for Entanglement Firewall with Executor

Tests that the firewall properly integrates with the quantum executor
to prevent unauthorized cross-tenant entanglement during circuit execution.
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


class TestFirewallIntegration(unittest.TestCase):
    """Test firewall integration with executor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.firewall = EntanglementGraph()
        self.executor = EnhancedExecutor(
            max_physical_qubits=1000,
            entanglement_firewall=self.firewall,
            require_certification=False,  # Test runtime firewall only
            caps={"CAP_ALLOC": True, "CAP_MEASURE": True}  # Old-style caps
        )
    
    def test_same_tenant_cnot_allowed(self):
        """Test that same-tenant CNOT is allowed."""
        # Create QVM graph with same-tenant CNOT
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0", "vq1"],
                        "args": {
                            "profile": "logical:surface_code(d=7)",
                            "tenant_id": "tenant_a"
                        }
                    },
                    {
                        "id": "n2",
                        "op": "APPLY_CNOT",
                        "vqs": ["vq0", "vq1"],
                        "args": {}
                    }
                ]
            }
        }
        
        # Should execute successfully
        result = self.executor.execute(qvm_graph)
        self.assertEqual(result["status"], "COMPLETED")
        
        # Check firewall statistics
        stats = self.firewall.get_statistics()
        self.assertEqual(stats["total_entanglements"], 1)
        self.assertEqual(stats["cross_tenant_entanglements"], 0)
        self.assertEqual(stats["firewall_violations"], 0)
    
    def test_cross_tenant_cnot_without_channel_blocked(self):
        """Test that cross-tenant CNOT without channel is blocked."""
        # Create QVM graph with cross-tenant CNOT (no channel)
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
                        "args": {}  # No channel!
                    }
                ]
            }
        }
        
        # Should raise EntanglementFirewallViolation
        with self.assertRaises(EntanglementFirewallViolation):
            self.executor.execute(qvm_graph)
        
        # Check firewall statistics
        stats = self.firewall.get_statistics()
        self.assertEqual(stats["firewall_violations"], 1)
        self.assertEqual(stats["cross_tenant_entanglements"], 0)


if __name__ == '__main__':
    unittest.main()
