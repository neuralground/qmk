"""
Integration tests for enhanced executor
"""

import unittest
import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from kernel.executor.enhanced_executor import EnhancedExecutor
from tests.test_helpers import create_test_executor


class TestEnhancedExecutor(unittest.TestCase):
    """Test enhanced QVM graph executor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = create_test_executor(seed=42)
    
    def test_simple_bell_state(self):
        """Test executing simple Bell state preparation."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "alloc1",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:surface_code(d=5)"},
                        "vqs": ["q0", "q1"],
                        "caps": ["CAP_ALLOC"]
                    },
                    {
                        "id": "h1",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    },
                    {
                        "id": "cnot1",
                        "op": "APPLY_CNOT",
                        "vqs": ["q0", "q1"]
                    },
                    {
                        "id": "m1",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    },
                    {
                        "id": "m2",
                        "op": "MEASURE_Z",
                        "vqs": ["q1"],
                        "produces": ["m1"]
                    },
                    {
                        "id": "free1",
                        "op": "FREE_LQ",
                        "vqs": ["q0", "q1"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "chs": [],
                "events": ["m0", "m1"]
            },
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("m0", result["events"])
        self.assertIn("m1", result["events"])
        self.assertIn(result["events"]["m0"], [0, 1])
        self.assertIn(result["events"]["m1"], [0, 1])
    
    def test_single_qubit_gates(self):
        """Test all single-qubit gates."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"], "caps": ["CAP_ALLOC"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "s1", "op": "APPLY_S", "vqs": ["q0"]},
                    {"id": "x1", "op": "APPLY_X", "vqs": ["q0"]},
                    {"id": "y1", "op": "APPLY_Y", "vqs": ["q0"]},
                    {"id": "z1", "op": "APPLY_Z", "vqs": ["q0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
        # Qubit is freed at end, so check execution log instead
        self.assertGreater(len(result["execution_log"]), 0)
    
    def test_conditional_execution(self):
        """Test conditional execution with guards."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"], "caps": ["CAP_ALLOC"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "x1", "op": "APPLY_X", "vqs": ["q0"], "guard": {"event": "m0", "equals": 1}},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
        # Guard should have been evaluated
        self.assertIn("m0", result["events"])
    
    def test_cond_pauli(self):
        """Test COND_PAULI operation."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"], "caps": ["CAP_ALLOC"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "corr", "op": "COND_PAULI", "args": {"mask": "X"}, "vqs": ["q0"], "inputs": ["m0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
    
    def test_channel_operations(self):
        """Test channel open/close operations."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 2, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0", "q1"], "caps": ["CAP_ALLOC"]},
                    {"id": "open1", "op": "OPEN_CHAN", "args": {"fidelity": 0.99}, "vqs": ["q0", "q1"], "chs": ["ch0"], "caps": ["CAP_LINK"]},
                    {"id": "close1", "op": "CLOSE_CHAN", "chs": ["ch0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0", "q1"]}
                ]
            },
            "resources": {"vqs": ["q0", "q1"], "chs": ["ch0"], "events": []},
            "caps": ["CAP_ALLOC", "CAP_LINK"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
    
    def test_reset_operation(self):
        """Test RESET operation."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"], "caps": ["CAP_ALLOC"]},
                    {"id": "x1", "op": "APPLY_X", "vqs": ["q0"]},
                    {"id": "reset1", "op": "RESET", "vqs": ["q0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
        # After reset, measurement should give 0 (deterministic with seed)
    
    def test_telemetry_collection(self):
        """Test comprehensive telemetry collection."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 2, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0", "q1"], "caps": ["CAP_ALLOC"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "cnot1", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0", "q1"]}
                ]
            },
            "resources": {"vqs": ["q0", "q1"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        result = self.executor.execute(graph)
        
        telemetry = result["telemetry"]
        
        # Check resource usage
        self.assertIn("resource_usage", telemetry)
        self.assertEqual(telemetry["resource_usage"]["logical_qubits_allocated"], 0)  # Freed at end
        
        # Check qubit telemetry exists
        self.assertIn("qubits", telemetry)
        
        # Check simulation time advanced
        self.assertGreater(telemetry["simulation_time_us"], 0)
    
    def test_missing_capability(self):
        """Test execution fails with missing capability."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": []},
            "caps": []  # Missing CAP_ALLOC
        }
        
        # Create executor with CAP_ALLOC disabled
        executor = create_test_executor(seed=42, caps={"CAP_ALLOC": False})
        
        with self.assertRaises(RuntimeError) as ctx:
            executor.execute(graph)
        
        self.assertIn("Missing capabilities", str(ctx.exception))
    
    def test_deterministic_execution(self):
        """Test deterministic execution with same seed."""
        graph = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {"id": "alloc1", "op": "ALLOC_LQ", "args": {"n": 1, "profile": "logical:surface_code(d=5)"}, "vqs": ["q0"], "caps": ["CAP_ALLOC"]},
                    {"id": "h1", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "free1", "op": "FREE_LQ", "vqs": ["q0"]}
                ]
            },
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]},
            "caps": ["CAP_ALLOC"]
        }
        
        # First run
        executor1 = create_test_executor(seed=42)
        result1 = executor1.execute(graph)
        
        # Second run with same seed
        executor2 = create_test_executor(seed=42)
        result2 = executor2.execute(graph)
        
        # Should get same measurement outcome
        self.assertEqual(result1["events"]["m0"], result2["events"]["m0"])


class TestRealWorldGraphs(unittest.TestCase):
    """Test execution of real-world QVM graphs."""
    
    def test_load_and_execute_bell_state(self):
        """Test loading and executing bell_teleport_cnot.qvm.json."""
        graph_path = os.path.join(ROOT, "qvm/examples/bell_teleport_cnot.qvm.json")
        
        if not os.path.exists(graph_path):
            self.skipTest("Example graph not found")
        
        with open(graph_path) as f:
            graph = json.load(f)
        
        executor = create_test_executor(seed=42)
        result = executor.execute(graph)
        
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("events", result)
        self.assertIn("telemetry", result)


if __name__ == "__main__":
    unittest.main()
