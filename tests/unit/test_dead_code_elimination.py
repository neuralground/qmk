#!/usr/bin/env python3
"""Tests for dead code elimination."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from kernel.qir_bridge.optimizer.passes import DeadCodeEliminationPass


class TestDeadCodeElimination(unittest.TestCase):
    """Test dead code elimination optimization."""
    
    def test_remove_unmeasured_qubit_operations(self):
        """Test removing operations on unmeasured qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # q0 is measured, q1 is not
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))  # Dead code
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))  # Dead code
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        self.assertEqual(circuit.get_gate_count(), 3)
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should remove q1 operations
        self.assertEqual(result.get_gate_count(), 1)  # Only H on q0
        self.assertEqual(opt_pass.metrics.gates_removed, 2)
    
    def test_keep_operations_affecting_measured_qubits(self):
        """Test keeping operations that affect measured qubits via CNOT."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # q1 affects q0 via CNOT, so q1 operations are live
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should keep all operations
        self.assertEqual(result.get_gate_count(), 2)
        self.assertEqual(opt_pass.metrics.gates_removed, 0)
    
    def test_remove_operations_after_measurement(self):
        """Test removing operations after final measurement."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))  # Dead code
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))  # Dead code
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should remove operations after measurement
        self.assertEqual(result.get_gate_count(), 1)  # Only H before measurement
        self.assertEqual(opt_pass.metrics.gates_removed, 2)
    
    def test_no_removal_when_all_measured(self):
        """Test that nothing is removed when all qubits are measured."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q1], result='m1'))
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should keep everything
        self.assertEqual(result.get_gate_count(), 2)
        self.assertEqual(opt_pass.metrics.gates_removed, 0)
    
    def test_complex_dependency_chain(self):
        """Test complex dependency chains."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # q2 affects q1, q1 affects q0, only q0 is measured
        # All should be kept
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q2, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q1, q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should keep all operations
        self.assertEqual(result.get_gate_count(), 3)
    
    def test_unused_ancilla(self):
        """Test removing unused ancilla qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')  # Ancilla, never used
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))  # Dead
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(opt_pass.metrics.qubit_reduction, 1)
    
    def test_no_measurements_keeps_everything(self):
        """Test that without measurements, everything is kept (conservative)."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Without measurements, we're conservative and keep everything
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_multiple_measurements_same_qubit(self):
        """Test handling multiple measurements on same qubit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m1'))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))  # After last measurement
        
        opt_pass = DeadCodeEliminationPass()
        result = opt_pass.run(circuit)
        
        # Should keep operations between measurements, remove after last
        self.assertEqual(result.get_gate_count(), 2)  # H and X


if __name__ == '__main__':
    unittest.main()
