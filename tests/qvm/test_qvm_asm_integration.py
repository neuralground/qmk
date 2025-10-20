#!/usr/bin/env python3
"""
Integration tests for QVM assembly system.
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qvm.tools.qvm_asm import assemble
from qvm.tools.qvm_disasm import disassemble


class TestQVMAssemblyIntegration(unittest.TestCase):
    """Test QVM assembly integration."""
    
    def test_assemble_bell_state(self):
        """Test assembling Bell state."""
        asm = """
        .version 0.1
        
        h: APPLY_H q0
        cnot: APPLY_CNOT q0, q1
        m0: MEASURE_Z q0 -> m0
        m1: MEASURE_Z q1 -> m1
        """
        
        qvm = assemble(asm)
        
        self.assertEqual(qvm["version"], "0.1")
        self.assertEqual(len(qvm["program"]["nodes"]), 4)
        self.assertIn("q0", qvm["resources"]["vqs"])
        self.assertIn("q1", qvm["resources"]["vqs"])
    
    def test_assemble_with_guards(self):
        """Test assembling with conditional operations."""
        asm = """
        .version 0.1
        
        m: MEASURE_Z q0 -> m0
        corr: APPLY_X q1 if m0==1
        """
        
        qvm = assemble(asm)
        
        self.assertEqual(len(qvm["program"]["nodes"]), 2)
        self.assertIn("guard", qvm["program"]["nodes"][1])
    
    def test_roundtrip_conversion(self):
        """Test assembly -> disassembly -> assembly."""
        asm1 = """
        .version 0.1
        
        h: APPLY_H q0
        x: APPLY_X q0
        """
        
        qvm1 = assemble(asm1)
        asm2 = disassemble(qvm1)
        qvm2 = assemble(asm2)
        
        self.assertEqual(qvm1["version"], qvm2["version"])
        self.assertEqual(len(qvm1["program"]["nodes"]), len(qvm2["program"]["nodes"]))


if __name__ == '__main__':
    unittest.main()
