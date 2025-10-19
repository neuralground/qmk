#!/usr/bin/env python3
"""Tests for gate commutation optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from qir.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from qir.optimizer.passes import GateCommutationPass, GateCancellationPass


class TestGateCommutation(unittest.TestCase):
    """Test gate commutation optimization."""
    
    def test_commute_different_qubits(self):
        """Test commuting gates on different qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H(q0) → X(q1) → H(q0)
        # Should commute X forward: X(q1) → H(q0) → H(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 3)
        
        # Run commutation
        opt_pass = GateCommutationPass()
        result = opt_pass.run(circuit)
        
        # Should have moved gates together
        # Check that the two H gates are now adjacent
        h_indices = [i for i, inst in enumerate(result.instructions) 
                    if inst.inst_type == InstructionType.H]
        
        if len(h_indices) == 2:
            # They should be adjacent (or close)
            self.assertLessEqual(abs(h_indices[1] - h_indices[0]), 1)
    
    def test_commutation_enables_cancellation(self):
        """Test that commutation enables cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H(q0) → X(q1) → H(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 3)
        
        # Run commutation + cancellation
        manager = PassManager([
            GateCommutationPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # Should end up with just X(q1)
        self.assertEqual(result.get_gate_count(), 1)
        self.assertEqual(result.instructions[0].inst_type, InstructionType.X)
    
    def test_no_commutation_same_qubit_non_commuting(self):
        """Test that non-commuting gates on same qubit don't commute."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H(q0) → X(q0) → H(q0)
        # H and X don't commute, so no reordering
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        original_order = [inst.inst_type for inst in circuit.instructions]
        
        opt_pass = GateCommutationPass()
        result = opt_pass.run(circuit)
        
        result_order = [inst.inst_type for inst in result.instructions]
        
        # Order should be unchanged
        self.assertEqual(original_order, result_order)
    
    def test_commute_phase_gates(self):
        """Test commuting phase gates on same qubit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Z(q0) → X(q1) → S(q0)
        # Z and S commute, so this could enable optimizations
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        opt_pass = GateCommutationPass()
        result = opt_pass.run(circuit)
        
        # Should still have 3 gates
        self.assertEqual(result.get_gate_count(), 3)
    
    def test_multiple_commutations(self):
        """Test multiple commutation opportunities."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # H(q0) → X(q1) → Y(q2) → H(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.Y, [q2]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # Run commutation + cancellation
        manager = PassManager([
            GateCommutationPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # Should cancel H gates, leaving X and Y
        self.assertEqual(result.get_gate_count(), 2)
    
    def test_max_distance_limit(self):
        """Test that commutation respects max distance."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H(q0) → many gates on q1 → H(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # Add 10 gates on q1 (more than default max_distance)
        for _ in range(10):
            circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # With default max_distance=5, shouldn't commute
        opt_pass = GateCommutationPass(max_distance=5)
        result = opt_pass.run(circuit)
        
        # Gates should still be far apart
        h_indices = [i for i, inst in enumerate(result.instructions) 
                    if inst.inst_type == InstructionType.H]
        
        if len(h_indices) == 2:
            distance = abs(h_indices[1] - h_indices[0])
            self.assertGreater(distance, 5)
    
    def test_cnot_commutation_same_control(self):
        """Test CNOT commutation with same control."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        q2 = circuit.add_qubit('q2')
        
        # CNOT(q0,q1) and CNOT(q0,q2) commute (same control, different target)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q2]))
        
        opt_pass = GateCommutationPass()
        result = opt_pass.run(circuit)
        
        # Should still have 3 gates
        self.assertEqual(result.get_gate_count(), 3)
    
    def test_with_measurements(self):
        """Test that measurements don't commute with gates on same qubit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H(q0) → MEASURE(q0) → H(q0)
        # Measurement doesn't commute with H
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        original_order = [(inst.inst_type, inst.qubits) for inst in circuit.instructions]
        
        opt_pass = GateCommutationPass()
        result = opt_pass.run(circuit)
        
        result_order = [(inst.inst_type, inst.qubits) for inst in result.instructions]
        
        # Order should be unchanged
        self.assertEqual(original_order, result_order)


class TestCommutationWithCancellation(unittest.TestCase):
    """Test commutation combined with cancellation."""
    
    def test_full_optimization_pipeline(self):
        """Test complete optimization with commutation and cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Complex circuit with opportunities
        # H(q0) → X(q1) → H(q0) → Y(q1) → X(q1) → X(q1)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Y, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        self.assertEqual(circuit.get_gate_count(), 6)
        
        # Run multiple passes
        manager = PassManager([
            GateCommutationPass(),
            GateCancellationPass(),
            GateCommutationPass(),  # Run again after cancellation
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # Should significantly reduce gate count
        self.assertLess(result.get_gate_count(), 6)


if __name__ == '__main__':
    unittest.main()
