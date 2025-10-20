#!/usr/bin/env python3
"""
Tests for QVM Assembly Macro Preprocessor
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qvm.tools.qvm_asm_macros import preprocess


class TestMacroPreprocessor(unittest.TestCase):
    """Test macro preprocessing features."""
    
    def test_variable_substitution(self):
        """Test basic variable substitution."""
        asm = """
.set n = 4
.set prefix = "q"
h0: APPLY_H {prefix}{n}
"""
        result = preprocess(asm)
        self.assertIn("h0: APPLY_H q4", result)
    
    def test_for_loop_range(self):
        """Test .for loop with range."""
        asm = """
.set n = 3
.for i in 0..n-1
    h{i}: APPLY_H q{i}
.endfor
"""
        result = preprocess(asm)
        self.assertIn("h0: APPLY_H q0", result)
        self.assertIn("h1: APPLY_H q1", result)
        self.assertIn("h2: APPLY_H q2", result)
        self.assertNotIn(".for", result)
        self.assertNotIn(".endfor", result)
    
    def test_for_loop_list(self):
        """Test .for loop with list."""
        asm = """
.set qubits = ["q0", "q1", "q2"]
.for q in qubits
    h_{q}: APPLY_H {q}
.endfor
"""
        result = preprocess(asm)
        self.assertIn("h_q0: APPLY_H q0", result)
        self.assertIn("h_q1: APPLY_H q1", result)
        self.assertIn("h_q2: APPLY_H q2", result)
    
    def test_conditional_if(self):
        """Test .if conditional."""
        asm = """
.set use_hadamard = True
.if use_hadamard
    h0: APPLY_H q0
.endif
"""
        result = preprocess(asm)
        self.assertIn("h0: APPLY_H q0", result)
        self.assertNotIn(".if", result)
    
    def test_conditional_if_else(self):
        """Test .if/.else conditional."""
        asm = """
.set oracle_type = "constant"
.if oracle_type == "constant"
    ; Identity oracle
.else
    oracle: APPLY_X y
.endif
"""
        result = preprocess(asm)
        self.assertIn("; Identity oracle", result)
        self.assertNotIn("oracle: APPLY_X y", result)
    
    def test_macro_definition_and_call(self):
        """Test macro definition and expansion."""
        asm = """
.macro BELL_PAIR(q0, q1)
    h: APPLY_H {q0}
    cnot: APPLY_CNOT {q0}, {q1}
.endmacro

BELL_PAIR(qA, qB)
"""
        result = preprocess(asm)
        self.assertIn("h: APPLY_H qA", result)
        self.assertIn("cnot: APPLY_CNOT qA, qB", result)
        self.assertNotIn(".macro", result)
        self.assertNotIn(".endmacro", result)
    
    def test_nested_loops(self):
        """Test nested .for loops."""
        asm = """
.for i in 0..1
    .for j in 0..1
        gate{i}_{j}: APPLY_CNOT q{i}, q{j}
    .endfor
.endfor
"""
        result = preprocess(asm)
        self.assertIn("gate0_0: APPLY_CNOT q0, q0", result)
        self.assertIn("gate0_1: APPLY_CNOT q0, q1", result)
        self.assertIn("gate1_0: APPLY_CNOT q1, q0", result)
        self.assertIn("gate1_1: APPLY_CNOT q1, q1", result)
    
    def test_ghz_state_example(self):
        """Test realistic GHZ state generation."""
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.set n_qubits = 4
.set qubit_list = [f"q{i}" for i in range(n_qubits)]

alloc: ALLOC_LQ n={n_qubits}, profile="logical:Surface(d=3)" -> {", ".join(qubit_list)}

; Create GHZ state
h0: APPLY_H q0
.for i in 1..n_qubits-1
    cnot{i}: APPLY_CNOT q0, q{i}
.endfor

; Measure all
.for i in 0..n_qubits-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
"""
        result = preprocess(asm)
        self.assertIn(".version 0.1", result)
        self.assertIn("h0: APPLY_H q0", result)
        self.assertIn("cnot1: APPLY_CNOT q0, q1", result)
        self.assertIn("cnot2: APPLY_CNOT q0, q2", result)
        self.assertIn("cnot3: APPLY_CNOT q0, q3", result)
        self.assertIn("m0: MEASURE_Z q0 -> m0", result)
        self.assertIn("m3: MEASURE_Z q3 -> m3", result)
    
    @unittest.skip("TODO: Fix variable substitution inside conditionals")
    def test_grovers_oracle_macro(self):
        """Test Grover's oracle with conditionals."""
        asm = """
.set use_flip = True
.set qubits = ["q0", "q1"]

; Oracle: mark target state
.if use_flip
    flip1: APPLY_X {qubits[1]}
.endif

; Controlled-Z
h_cz: APPLY_H {qubits[1]}
cnot_cz: APPLY_CNOT {qubits[0]}, {qubits[1]}
h_cz2: APPLY_H {qubits[1]}

; Unflip
.if use_flip
    unflip1: APPLY_X {qubits[1]}
.endif
"""
        result = preprocess(asm)
        # Should include flip gates
        self.assertIn("flip1: APPLY_X q1", result)
        self.assertIn("h_cz: APPLY_H q1", result)
        self.assertIn("unflip1: APPLY_X q1", result)


class TestMacroIntegration(unittest.TestCase):
    """Test integration with assembler."""
    
    def test_assemble_with_macros(self):
        """Test that macros work with full assembler."""
        from qvm.tools.qvm_asm import assemble
        
        asm = """
.version 0.1
.caps CAP_ALLOC CAP_COMPUTE CAP_MEASURE

.set n = 2

alloc: ALLOC_LQ n={n}, profile="logical:Surface(d=3)" -> q0, q1

.for i in 0..n-1
    h{i}: APPLY_H q{i}
.endfor

cnot: APPLY_CNOT q0, q1

.for i in 0..n-1
    m{i}: MEASURE_Z q{i} -> m{i}
.endfor
"""
        result = assemble(asm)
        
        # Check structure
        self.assertEqual(result['version'], '0.1')
        self.assertIn('program', result)
        self.assertIn('nodes', result['program'])
        
        # Check nodes were created
        nodes = result['program']['nodes']
        node_ops = [n['op'] for n in nodes]
        
        self.assertIn('ALLOC_LQ', node_ops)
        self.assertEqual(node_ops.count('APPLY_H'), 2)
        self.assertIn('APPLY_CNOT', node_ops)
        self.assertEqual(node_ops.count('MEASURE_Z'), 2)


if __name__ == '__main__':
    unittest.main()
