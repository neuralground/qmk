#!/usr/bin/env python3
"""Tests for QVM assembler and disassembler."""

import unittest
import json
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from qvm.tools.qvm_asm import assemble
from qvm.tools.qvm_disasm import disassemble


class TestQVMAssembler(unittest.TestCase):
    """Test QVM assembler."""
    
    def test_simple_program(self):
        """Test assembling a simple program."""
        asm = """
        .version 0.1
        .caps CAP_ALLOC
        
        alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
        h: APPLY_H q0
        cnot: APPLY_CNOT q0, q1
        m0: MEASURE_Z q0 -> m0
        m1: MEASURE_Z q1 -> m1
        free: FREE_LQ q0, q1
        """
        
        result = assemble(asm)
        
        self.assertEqual(result["version"], "0.1")
        self.assertEqual(result["caps"], ["CAP_ALLOC"])
        self.assertEqual(len(result["program"]["nodes"]), 6)
        
        # Check first node
        alloc_node = result["program"]["nodes"][0]
        self.assertEqual(alloc_node["id"], "alloc")
        self.assertEqual(alloc_node["op"], "ALLOC_LQ")
        self.assertEqual(alloc_node["args"]["n"], 2)
        self.assertEqual(alloc_node["args"]["profile"], "logical:surface_code(d=3)")
        self.assertEqual(alloc_node["vqs"], ["q0", "q1"])
        self.assertEqual(alloc_node["caps"], ["CAP_ALLOC"])
        
        # Check resources
        self.assertIn("q0", result["resources"]["vqs"])
        self.assertIn("q1", result["resources"]["vqs"])
        self.assertIn("m0", result["resources"]["events"])
        self.assertIn("m1", result["resources"]["events"])
    
    def test_guards(self):
        """Test guard parsing."""
        asm = """
        .version 0.1
        
        m: MEASURE_Z q0 -> m0
        corr: APPLY_X q1 if m0==1
        """
        
        result = assemble(asm)
        
        corr_node = result["program"]["nodes"][1]
        self.assertEqual(corr_node["id"], "corr")
        self.assertIn("guard", corr_node)
        self.assertEqual(corr_node["guard"]["event"], "m0")
        self.assertEqual(corr_node["guard"]["equals"], 1)
    
    def test_and_guard(self):
        """Test AND guard parsing."""
        asm = """
        .version 0.1
        
        corr: APPLY_X q2 if m0==1 && m1==0
        """
        
        result = assemble(asm)
        
        node = result["program"]["nodes"][0]
        self.assertEqual(node["guard"]["type"], "and")
        self.assertEqual(len(node["guard"]["conditions"]), 2)
    
    def test_comments(self):
        """Test comment handling."""
        asm = """
        .version 0.1
        
        ; This is a comment
        alloc: ALLOC_LQ n=1 -> q0  ; inline comment
        """
        
        result = assemble(asm)
        
        self.assertEqual(len(result["program"]["nodes"]), 1)
        self.assertEqual(result["program"]["nodes"][0]["id"], "alloc")


class TestQVMDisassembler(unittest.TestCase):
    """Test QVM disassembler."""
    
    def test_simple_disassembly(self):
        """Test disassembling a simple program."""
        qvm = {
            "version": "0.1",
            "caps": ["CAP_ALLOC"],
            "program": {
                "nodes": [
                    {
                        "id": "alloc",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:surface_code(d=3)"},
                        "vqs": ["q0", "q1"],
                        "caps": ["CAP_ALLOC"]
                    },
                    {
                        "id": "h",
                        "op": "APPLY_H",
                        "vqs": ["q0"]
                    }
                ]
            },
            "resources": {
                "vqs": ["q0", "q1"],
                "chs": [],
                "events": []
            }
        }
        
        result = disassemble(qvm)
        
        self.assertIn(".version 0.1", result)
        self.assertIn(".caps CAP_ALLOC", result)
        self.assertIn("alloc: ALLOC_LQ", result)
        self.assertIn("h: APPLY_H q0", result)
    
    def test_guard_disassembly(self):
        """Test disassembling guards."""
        qvm = {
            "version": "0.1",
            "program": {
                "nodes": [
                    {
                        "id": "corr",
                        "op": "APPLY_X",
                        "vqs": ["q1"],
                        "guard": {"event": "m0", "equals": 1}
                    }
                ]
            },
            "resources": {"vqs": ["q1"], "chs": [], "events": []}
        }
        
        result = disassemble(qvm)
        
        self.assertIn("if m0==1", result)
    
    def test_outputs_disassembly(self):
        """Test disassembling outputs."""
        qvm = {
            "version": "0.1",
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
            "resources": {"vqs": ["q0"], "chs": [], "events": ["m0"]}
        }
        
        result = disassemble(qvm)
        
        self.assertIn("-> m0", result)


class TestRoundTrip(unittest.TestCase):
    """Test round-trip conversion."""
    
    def test_bell_state_roundtrip(self):
        """Test round-trip conversion of Bell state."""
        asm = """
        .version 0.1
        .caps CAP_ALLOC
        
        alloc: ALLOC_LQ n=2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
        h: APPLY_H q0
        cnot: APPLY_CNOT q0, q1
        m0: MEASURE_Z q0 -> m0
        m1: MEASURE_Z q1 -> m1
        free: FREE_LQ q0, q1
        """
        
        # Assemble to JSON
        qvm1 = assemble(asm)
        
        # Disassemble back to assembly
        asm2 = disassemble(qvm1)
        
        # Assemble again
        qvm2 = assemble(asm2)
        
        # Compare (should be identical)
        self.assertEqual(qvm1["version"], qvm2["version"])
        self.assertEqual(qvm1["caps"], qvm2["caps"])
        self.assertEqual(len(qvm1["program"]["nodes"]), len(qvm2["program"]["nodes"]))
        
        # Check each node
        for node1, node2 in zip(qvm1["program"]["nodes"], qvm2["program"]["nodes"]):
            self.assertEqual(node1["id"], node2["id"])
            self.assertEqual(node1["op"], node2["op"])
            if "vqs" in node1:
                self.assertEqual(node1["vqs"], node2["vqs"])
            if "args" in node1:
                self.assertEqual(node1["args"], node2["args"])
    
    def test_conditional_roundtrip(self):
        """Test round-trip with conditional operations."""
        asm = """
        .version 0.1
        
        m: MEASURE_Z q0 -> m0
        corr_x: APPLY_X q1 if m0==1
        corr_z: APPLY_Z q1 if m0==0
        """
        
        qvm1 = assemble(asm)
        asm2 = disassemble(qvm1)
        qvm2 = assemble(asm2)
        
        # Check guards preserved
        self.assertEqual(qvm1["program"]["nodes"][1]["guard"], 
                        qvm2["program"]["nodes"][1]["guard"])
        self.assertEqual(qvm1["program"]["nodes"][2]["guard"], 
                        qvm2["program"]["nodes"][2]["guard"])
    
    def test_existing_json_roundtrip(self):
        """Test round-trip with existing JSON examples."""
        json_file = os.path.join(ROOT, "qvm/examples/bell_teleport_cnot.qvm.json")
        
        if not os.path.exists(json_file):
            self.skipTest("Example file not found")
        
        with open(json_file) as f:
            qvm1 = json.load(f)
        
        # Disassemble
        asm = disassemble(qvm1)
        
        # Assemble back
        qvm2 = assemble(asm)
        
        # Compare key fields
        self.assertEqual(qvm1["version"], qvm2["version"])
        self.assertEqual(len(qvm1["program"]["nodes"]), len(qvm2["program"]["nodes"]))


if __name__ == "__main__":
    unittest.main()
