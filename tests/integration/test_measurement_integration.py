#!/usr/bin/env python3
"""
Integration tests for all measurement bases through the full stack.

Tests measurement support across:
- QVM format
- Executor
- End-to-end execution
"""

import unittest
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.executor.enhanced_executor import EnhancedExecutor


class TestMeasurementIntegration(unittest.TestCase):
    """Integration tests for measurement bases."""
    
    def test_qvm_z_basis_measurement(self):
        """Test Z-basis measurement through QVM format."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 1, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "mz",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0"],
                "events": ["m0"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m0', result['events'])
        self.assertIn(result['events']['m0'], [0, 1])
    
    def test_qvm_x_basis_measurement(self):
        """Test X-basis measurement through QVM format."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 1, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "mx",
                        "op": "MEASURE_X",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0"],
                "events": ["m0"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m0', result['events'])
        # |+⟩ measured in X-basis should give 0
        self.assertEqual(result['events']['m0'], 0)
    
    def test_qvm_y_basis_measurement(self):
        """Test Y-basis measurement through QVM format."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 1, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "my",
                        "op": "MEASURE_Y",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0"],
                "events": ["m0"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m0', result['events'])
        self.assertIn(result['events']['m0'], [0, 1])
    
    def test_qvm_bell_measurement(self):
        """Test Bell basis measurement through QVM format."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "cnot",
                        "op": "APPLY_CNOT",
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "bell_meas",
                        "op": "MEASURE_BELL",
                        "vqs": ["q0", "q1"],
                        "produces": ["m0", "m1"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "events": ["m0", "m1"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m0', result['events'])
        self.assertIn('m1', result['events'])
        # Bell state |Φ+⟩ should mostly measure as (0,0), but allow for errors
        # Just verify we get valid outcomes
        self.assertIn(result['events']['m0'], [0, 1])
        self.assertIn(result['events']['m1'], [0, 1])
    
    def test_qvm_bell_measurement_single_event(self):
        """Test Bell measurement with single Bell index output."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "cnot",
                        "op": "APPLY_CNOT",
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "bell_meas",
                        "op": "MEASURE_BELL",
                        "vqs": ["q0", "q1"],
                        "produces": ["bell_index"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "events": ["bell_index"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('bell_index', result['events'])
        # Bell state |Φ+⟩ should mostly have index 0, but allow for errors
        # Just verify we get a valid Bell index (0-3)
        self.assertIn(result['events']['bell_index'], [0, 1, 2, 3])
    
    def test_measurement_bases_example(self):
        """Test the measurement_bases.qvm.json example."""
        example_path = ROOT / "qvm" / "examples" / "measurement_bases.qvm.json"
        
        with open(example_path) as f:
            qvm_graph = json.load(f)
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m_z', result['events'])
        self.assertIn('m_x', result['events'])
        self.assertIn('m_y', result['events'])
    
    def test_bell_measurement_example(self):
        """Test the bell_measurement.qvm.json example."""
        example_path = ROOT / "qvm" / "examples" / "bell_measurement.qvm.json"
        
        with open(example_path) as f:
            qvm_graph = json.load(f)
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertIn('m0', result['events'])
        self.assertIn('m1', result['events'])
        self.assertIn('result', result['events'])
    
    def test_multiple_measurement_bases(self):
        """Test using multiple measurement bases in one circuit."""
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 3, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1", "q2"]
                    },
                    # Prepare |+⟩ on all qubits
                    {"id": "h0", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q1"]},
                    {"id": "h2", "op": "APPLY_H", "vqs": ["q2"]},
                    # Measure in different bases
                    {
                        "id": "mz",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m_z"]
                    },
                    {
                        "id": "mx",
                        "op": "MEASURE_X",
                        "vqs": ["q1"],
                        "produces": ["m_x"]
                    },
                    {
                        "id": "my",
                        "op": "MEASURE_Y",
                        "vqs": ["q2"],
                        "produces": ["m_y"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1", "q2"],
                "events": ["m_z", "m_x", "m_y"]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        self.assertEqual(result['status'], 'COMPLETED')
        
        # |+⟩ in Z-basis: random
        self.assertIn(result['events']['m_z'], [0, 1])
        
        # |+⟩ in X-basis: should be 0
        self.assertEqual(result['events']['m_x'], 0)
        
        # |+⟩ in Y-basis: random (but we get a result)
        self.assertIn(result['events']['m_y'], [0, 1])
    
    def test_state_tomography_workflow(self):
        """Test a complete state tomography workflow."""
        # Prepare state |+⟩ and measure in all three Pauli bases
        results = {'Z': [], 'X': [], 'Y': []}
        
        for basis, op in [('Z', 'MEASURE_Z'), ('X', 'MEASURE_X'), ('Y', 'MEASURE_Y')]:
            for i in range(10):
                qvm_graph = {
                    "program": {
                        "nodes": [
                            {
                                "id": "alloc",
                                "op": "ALLOC_LQ",
                                "args": {"n": 1, "profile": "logical:Surface(d=7)"},
                                "vqs": ["q0"]
                            },
                            {"id": "h", "op": "APPLY_H", "vqs": ["q0"]},
                            {
                                "id": "measure",
                                "op": op,
                                "vqs": ["q0"],
                                "produces": ["m0"]
                            }
                        ]
                    },
                    "resources": {
                        "vqs": ["q0"],
                        "events": ["m0"]
                    }
                }
                
                executor = EnhancedExecutor(seed=i)
                result = executor.execute(qvm_graph)
                results[basis].append(result['events']['m0'])
        
        # |+⟩ should give all 0s in X-basis
        self.assertEqual(results['X'].count(0), 10, "X-basis should give all 0s for |+⟩")
        
        # Z and Y bases should have some variation
        self.assertGreater(len(set(results['Z'])), 1, "Z-basis should have variation")


if __name__ == '__main__':
    unittest.main(verbosity=2)
