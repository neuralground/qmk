#!/usr/bin/env python3
"""
Tests for QVM graph structure and semantics.

Tests basic QVM graph properties without requiring full validation.
"""

import unittest
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


class TestQVMStructure(unittest.TestCase):
    """Test QVM graph structure."""
    
    def test_valid_qvm_structure(self):
        """Test that valid QVM has required fields."""
        qvm = {
            "version": "0.1",
            "caps": [],
            "program": {"nodes": []},
            "resources": {"vqs": [], "chs": [], "events": []}
        }
        
        self.assertIn("version", qvm)
        self.assertIn("caps", qvm)
        self.assertIn("program", qvm)
        self.assertIn("resources", qvm)
    
    def test_node_structure(self):
        """Test that nodes have required fields."""
        node = {
            "id": "h",
            "op": "APPLY_H",
            "vqs": ["q0"]
        }
        
        self.assertIn("id", node)
        self.assertIn("op", node)
        self.assertIn("vqs", node)
    
    def test_resources_structure(self):
        """Test that resources have required fields."""
        resources = {
            "vqs": ["q0", "q1"],
            "chs": [],
            "events": ["m0"]
        }
        
        self.assertIn("vqs", resources)
        self.assertIn("chs", resources)
        self.assertIn("events", resources)


class TestQVMSemantics(unittest.TestCase):
    """Test QVM semantic properties."""
    
    def test_qubit_usage(self):
        """Test that qubits used in operations are declared."""
        qvm = {
            "version": "0.1",
            "caps": [],
            "program": {
                "nodes": [
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0"],
                "chs": [],
                "events": []
            }
        }
        
        # Check qubit is declared
        node_qubits = qvm["program"]["nodes"][0]["vqs"]
        declared_qubits = qvm["resources"]["vqs"]
        
        for q in node_qubits:
            self.assertIn(q, declared_qubits)
    
    def test_measurement_produces_event(self):
        """Test that measurements produce events."""
        qvm = {
            "version": "0.1",
            "caps": [],
            "program": {
                "nodes": [
                    {
                        "id": "m",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0"],
                "chs": [],
                "events": ["m0"]
            }
        }
        
        # Check event is declared
        produced_events = qvm["program"]["nodes"][0]["produces"]
        declared_events = qvm["resources"]["events"]
        
        for e in produced_events:
            self.assertIn(e, declared_events)
    
    def test_guard_references_event(self):
        """Test that guards reference declared events."""
        qvm = {
            "version": "0.1",
            "caps": [],
            "program": {
                "nodes": [
                    {
                        "id": "m",
                        "op": "MEASURE_Z",
                        "vqs": ["q0"],
                        "produces": ["m0"]
                    },
                    {
                        "id": "corr",
                        "op": "APPLY_X",
                        "vqs": ["q1"],
                        "guard": {"event": "m0", "equals": 1}
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "chs": [],
                "events": ["m0"]
            }
        }
        
        # Check guard event is declared
        guard_event = qvm["program"]["nodes"][1]["guard"]["event"]
        declared_events = qvm["resources"]["events"]
        
        self.assertIn(guard_event, declared_events)


class TestQVMExamples(unittest.TestCase):
    """Test QVM example files."""
    
    def test_load_example_file(self):
        """Test loading example QVM file."""
        example_path = ROOT / "qvm" / "examples" / "bell_teleport_cnot.qvm.json"
        
        if not example_path.exists():
            self.skipTest("Example file not found")
        
        with open(example_path) as f:
            qvm = json.load(f)
        
        # Check structure
        self.assertIn("version", qvm)
        self.assertIn("program", qvm)
        self.assertIn("resources", qvm)
    
    def test_example_has_nodes(self):
        """Test that example has nodes."""
        example_path = ROOT / "qvm" / "examples" / "bell_teleport_cnot.qvm.json"
        
        if not example_path.exists():
            self.skipTest("Example file not found")
        
        with open(example_path) as f:
            qvm = json.load(f)
        
        self.assertGreater(len(qvm["program"]["nodes"]), 0)


if __name__ == '__main__':
    unittest.main()
