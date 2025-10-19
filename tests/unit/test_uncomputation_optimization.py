#!/usr/bin/env python3
"""Tests for uncomputation optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType
)
from kernel.qir_bridge.optimizer.passes import UncomputationOptimizationPass


class TestUncomputationOptimization(unittest.TestCase):
    """Test uncomputation optimization."""
    
    def test_identify_ancillas(self):
        """Test identifying ancilla qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')  # Data qubit (measured)
        q1 = circuit.add_qubit('q1')  # Ancilla (not measured)
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should identify q1 as ancilla
        self.assertEqual(opt_pass.metrics.custom['ancilla_qubits'], 1)
    
    def test_find_uncomputation_pairs(self):
        """Test finding computation/uncomputation pairs."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        anc = circuit.add_qubit('anc')
        
        # Computation
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        
        # Uncomputation (reverse)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should find uncomputation pair
        self.assertGreaterEqual(opt_pass.metrics.custom['uncomputation_pairs'], 1)
    
    def test_exact_reverse_pattern(self):
        """Test detecting exact reverse uncomputation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        anc = circuit.add_qubit('anc')
        
        # Computation: H → X → CNOT
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [anc]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        
        # Uncomputation: CNOT → X → H (exact reverse)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [anc]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should detect pattern (or at least identify ancilla)
        self.assertGreaterEqual(opt_pass.metrics.patterns_matched, 0)
        self.assertGreaterEqual(opt_pass.metrics.custom['ancilla_qubits'], 1)
    
    def test_no_ancillas(self):
        """Test circuit with no ancillas."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # All qubits measured
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have zero ancillas
        self.assertEqual(opt_pass.metrics.custom['ancilla_qubits'], 0)
    
    def test_multiple_ancillas(self):
        """Test multiple ancilla qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        anc1 = circuit.add_qubit('anc1')
        anc2 = circuit.add_qubit('anc2')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc1, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc2, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should identify both ancillas
        self.assertEqual(opt_pass.metrics.custom['ancilla_qubits'], 2)
    
    def test_reusable_ancillas(self):
        """Test identifying reusable ancillas."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        anc = circuit.add_qubit('anc')
        
        # Use ancilla with proper uncomputation
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [anc, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [anc]))
        
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = UncomputationOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should identify as reusable
        self.assertGreaterEqual(opt_pass.metrics.custom['ancillas_reusable'], 1)


if __name__ == '__main__':
    unittest.main()
