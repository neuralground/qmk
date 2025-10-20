#!/usr/bin/env python3
"""
Fuzz testing for QVM validator.

Tests validator robustness with random/malformed inputs.
"""

import unittest
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qvm.static_verifier import verify_qvm_graph


class TestQVMFuzzing(unittest.TestCase):
    """Fuzz testing for QVM validator."""
    
    def test_empty_graph(self):
        """Test with completely empty graph."""
        qvm = {}
        result = verify_qvm_graph(qvm)
        # Should handle gracefully (may have errors, but shouldn't crash)
        self.assertIsNotNone(result)
    
    def test_missing_version(self):
        """Test with missing version field."""
        qvm = {
            "program": {"nodes": []},
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_invalid_version_type(self):
        """Test with invalid version type."""
        qvm = {
            "version": 123,  # Should be string
            "program": {"nodes": []},
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_missing_program(self):
        """Test with missing program field."""
        qvm = {
            "version": "0.1",
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_invalid_program_type(self):
        """Test with invalid program type."""
        qvm = {
            "version": "0.1",
            "program": "not a dict",  # Should be dict
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_missing_nodes(self):
        """Test with missing nodes in program."""
        qvm = {
            "version": "0.1",
            "program": {},  # No nodes
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_invalid_nodes_type(self):
        """Test with invalid nodes type."""
        qvm = {
            "version": "0.1",
            "program": {"nodes": "not a list"},  # Should be list
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_node_missing_id(self):
        """Test node without ID."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        # Missing "id"
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_node_missing_op(self):
        """Test node without operation."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "h",
                        # Missing "op"
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_invalid_operation(self):
        """Test with invalid operation name."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "invalid",
                        "op": "INVALID_OP",  # Not a valid operation
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_undefined_qubit(self):
        """Test using undefined qubit."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q_undefined"]  # Not in resources
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        self.assertFalse(result.is_valid)
    
    def test_random_string_fields(self):
        """Test with random strings in various fields."""
        for _ in range(10):
            qvm = {
                "version": self._random_string(),
                "program": {
                    "nodes": [
                        {
                            "id": self._random_string(),
                            "op": self._random_string(),
                            "vqs": [self._random_string()]
                        }
                    ]
                },
                "resources": {
                    "vqs": [self._random_string()],
                    "chs": [],
                    "events": []
                }
            }
            result = verify_qvm_graph(qvm)
            # Should not crash
            self.assertIsNotNone(result)
    
    def test_deeply_nested_structure(self):
        """Test with deeply nested structures."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "n",
                        "op": "APPLY_H",
                        "vqs": ["q0"],
                        "metadata": {
                            "level1": {
                                "level2": {
                                    "level3": {
                                        "level4": "deep"
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_very_large_node_count(self):
        """Test with very large number of nodes."""
        nodes = []
        for i in range(1000):
            nodes.append({
                "id": f"n{i}",
                "op": "APPLY_H",
                "vqs": ["q0"]
            })
        
        qvm = {
            "version": "0.1",
            "program": {"nodes": nodes},
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle large graphs
        self.assertIsNotNone(result)
    
    def test_circular_dependencies(self):
        """Test with circular guard dependencies."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "m1",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["e1"],
                        "guard": {"event": "e2", "equals": 1}  # Depends on e2
                    },
                    {
                        "id": "m2",
                        "op": "MEASURE_Z",
                        "vqs": ["q1"],
                        "produces": ["e2"],
                        "guard": {"event": "e1", "equals": 1}  # Depends on e1
                    }
                ]
            },
            "resources": {"vqs": ["q0", "q1"], "chs": [], "events": ["e1", "e2"]}
        }
        result = verify_qvm_graph(qvm)
        # Should detect circular dependency
        self.assertFalse(result.is_valid)
    
    def test_null_values(self):
        """Test with null/None values."""
        qvm = {
            "version": None,
            "program": None,
            "resources": None
        }
        result = verify_qvm_graph(qvm)
        # Should handle gracefully
        self.assertIsNotNone(result)
    
    def test_unicode_strings(self):
        """Test with unicode characters."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "测试",  # Chinese characters
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []}
        }
        result = verify_qvm_graph(qvm)
        # Should handle unicode
        self.assertIsNotNone(result)
    
    def test_special_characters_in_ids(self):
        """Test with special characters in IDs."""
        special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
        for char in special_chars:
            qvm = {
                "version": "0.1",
                "program": {
                    "nodes": [
                        {
                            "id": f"node{char}",
                            "op": "APPLY_H",
                            "vqs": ["q0"]
                        }
                    ]
                },
                "resources": {"vqs": ["q0"], "chs": [], "events": []}
            }
            result = verify_qvm_graph(qvm)
            # Should handle special characters
            self.assertIsNotNone(result)
    
    # Helper methods
    
    def _random_string(self, length=10):
        """Generate random string."""
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(chars) for _ in range(length))


if __name__ == '__main__':
    unittest.main()
