#!/usr/bin/env python3
"""Tests for template matching."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from kernel.qir_bridge.optimizer.passes import TemplateMatchingPass


class TestTemplateMatching(unittest.TestCase):
    """Test template matching optimization."""
    
    def test_h_x_h_to_z(self):
        """Test H-X-H → Z template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H → X → H
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 3)
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should replace with Z
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.Z)
        self.assertEqual(opt_pass.metrics.patterns_matched, 1)
    
    def test_h_z_h_to_x(self):
        """Test H-Z-H → X template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should replace with X
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.X)
    
    def test_s_four_to_identity(self):
        """Test S^4 → Identity template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Four S gates = identity
        for _ in range(4):
            circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 4)
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should remove all gates
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_t_eight_to_identity(self):
        """Test T^8 → Identity template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Eight T gates = identity
        for _ in range(8):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should remove all gates
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_x_h_x_h_to_z(self):
        """Test X-H-X-H → Z template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should replace with Z
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.Z)
    
    def test_no_match_different_pattern(self):
        """Test that non-matching patterns are not replaced."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H → X (no H at end, shouldn't match)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        initial_count = circuit.get_gate_count()
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should not change
        self.assertEqual(result.get_gate_count(), initial_count)
        self.assertEqual(opt_pass.metrics.patterns_matched, 0)
    
    def test_multiple_templates_in_circuit(self):
        """Test multiple template matches in one circuit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H-X-H on q0 (→ Z)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # H-Z-H on q1 (→ X)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        self.assertEqual(circuit.get_gate_count(), 6)
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should replace both patterns
        self.assertEqual(result.get_gate_count(), 2)
        self.assertEqual(opt_pass.metrics.patterns_matched, 2)
    
    def test_iterative_matching(self):
        """Test that templates can match iteratively."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Create a pattern that needs multiple iterations
        # S → S → S → S → S → S → S → S
        # First iteration: S^4 → Identity (removes 4)
        # Second iteration: S^4 → Identity (removes remaining 4)
        for _ in range(8):
            circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should remove all
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_cnot_h_sequence_to_swap(self):
        """Test CNOT-H sequence → SWAP template."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # CNOT → H → H → CNOT → H → H
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        self.assertEqual(circuit.get_gate_count(), 6)
        
        opt_pass = TemplateMatchingPass()
        result = opt_pass.run(circuit)
        
        # Should replace with SWAP
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.SWAP)


if __name__ == '__main__':
    unittest.main()
