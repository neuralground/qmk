"""
Tests for QVM Static Verifier

Tests comprehensive static verification before execution.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qvm.static_verifier import (
    QVMStaticVerifier,
    VerificationError,
    VerificationErrorType,
    verify_qvm_graph
)


class TestStaticVerifier(unittest.TestCase):
    """Test QVM static verifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.verifier = QVMStaticVerifier(strict_mode=False)
    
    def test_valid_simple_graph(self):
        """Test verification of valid simple graph."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {"profile": "logical:surface_code(d=7)"}
                    },
                    {
                        "id": "n2",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    },
                    {
                        "id": "n3",
                        "op": "MEASURE_Z",
                        "vqs": ["vq0"],
                        "produces": ["ev0"],
                        "args": {}
                    }
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_use_before_allocation_rejected(self):
        """Test that using qubit before allocation is rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(
            result.errors[0].error_type,
            VerificationErrorType.LINEARITY_VIOLATION.value
        )
    
    def test_use_after_consume_rejected(self):
        """Test that use-after-consume is rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
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
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_double_allocation_rejected(self):
        """Test that double allocation is rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_double_measurement_rejected(self):
        """Test that double measurement is rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
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
        
        result = self.verifier.verify_graph(graph)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_resource_leak_warning(self):
        """Test that resource leaks generate warnings."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
                    },
                    {
                        "id": "n2",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                    # No measurement or free - leak!
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        # Valid in non-strict mode, but has warning
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("leak", result.warnings[0].lower())
    
    def test_missing_capability_rejected(self):
        """Test that missing capabilities are rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
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
        
        # Provide capabilities without CAP_MEASURE
        available_caps = {"CAP_ALLOC"}
        
        result = self.verifier.verify_graph(graph, available_caps)
        self.assertFalse(result.is_valid)
        
        # Should have capability error
        cap_errors = [e for e in result.errors 
                     if e.error_type == VerificationErrorType.CAPABILITY_MISSING.value]
        self.assertGreater(len(cap_errors), 0)
    
    def test_cross_tenant_without_channel_rejected(self):
        """Test that cross-tenant entanglement without channel is rejected."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {"tenant_id": "tenant_a"}
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq1"],
                        "args": {"tenant_id": "tenant_b"}
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
        
        result = self.verifier.verify_graph(graph)
        self.assertFalse(result.is_valid)
        
        # Should have firewall error
        firewall_errors = [e for e in result.errors 
                          if e.error_type == VerificationErrorType.FIREWALL_VIOLATION.value]
        self.assertGreater(len(firewall_errors), 0)
    
    def test_cross_tenant_with_channel_allowed(self):
        """Test that cross-tenant entanglement with channel is allowed."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {"tenant_id": "tenant_a"}
                    },
                    {
                        "id": "n2",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq1"],
                        "args": {"tenant_id": "tenant_b"}
                    },
                    {
                        "id": "n3",
                        "op": "APPLY_CNOT",
                        "vqs": ["vq0", "vq1"],
                        "args": {"channel": "ch1"}  # Has channel!
                    },
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
        
        result = self.verifier.verify_graph(graph)
        # Should be valid (no firewall errors)
        firewall_errors = [e for e in result.errors 
                          if e.error_type == VerificationErrorType.FIREWALL_VIOLATION.value]
        self.assertEqual(len(firewall_errors), 0)
    
    def test_certification(self):
        """Test graph certification."""
        valid_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
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
        
        is_certified, result = self.verifier.certify_graph(valid_graph)
        self.assertTrue(is_certified)
        self.assertTrue(result.is_valid)
    
    def test_certification_report(self):
        """Test certification report generation."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "APPLY_H",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                ]
            }
        }
        
        result = self.verifier.verify_graph(graph)
        report = self.verifier.get_certification_report(result)
        
        self.assertIn("CERTIFICATION REPORT", report)
        self.assertIn("REJECTED", report)
        self.assertGreater(len(report), 100)
    
    def test_strict_mode(self):
        """Test strict mode treats warnings as errors."""
        strict_verifier = QVMStaticVerifier(strict_mode=True)
        
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
                    }
                    # No consumption - leak warning
                ]
            }
        }
        
        result = strict_verifier.verify_graph(graph)
        # In strict mode, warnings become errors
        self.assertFalse(result.is_valid)
    
    def test_complex_valid_graph(self):
        """Test verification of complex valid graph."""
        graph = {
            "program": {
                "nodes": [
                    # Allocate
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0", "vq1"],
                        "args": {"tenant_id": "tenant_a"}
                    },
                    # Gates
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
                    # Measure
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
        
        result = self.verifier.verify_graph(graph)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)


class TestConvenienceFunction(unittest.TestCase):
    """Test convenience verification function."""
    
    def test_verify_qvm_graph(self):
        """Test quick verification function."""
        graph = {
            "program": {
                "nodes": [
                    {
                        "id": "n1",
                        "op": "ALLOC_LQ",
                        "vqs": ["vq0"],
                        "args": {}
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
        
        result = verify_qvm_graph(graph)
        self.assertTrue(result.is_valid)


if __name__ == '__main__':
    unittest.main()
