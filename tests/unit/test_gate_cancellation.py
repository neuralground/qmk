#!/usr/bin/env python3
"""Tests for gate cancellation optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from kernel.qir_bridge.optimizer.passes import GateCancellationPass


class TestGateCancellation(unittest.TestCase):
    """Test gate cancellation optimization."""
    
    def test_self_inverse_h_gate(self):
        """Test H → H cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Add H → H
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        self.assertEqual(circuit.get_gate_count(), 2)
        
        # Run optimization
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
        self.assertEqual(opt_pass.metrics.gates_removed, 2)
    
    def test_self_inverse_x_gate(self):
        """Test X → X cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_cnot_cancellation(self):
        """Test CNOT → CNOT cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
        self.assertEqual(opt_pass.metrics.cnot_removed, 2)
    
    def test_s_sdg_cancellation(self):
        """Test S → S† cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.SDG, [q0]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_t_tdg_cancellation(self):
        """Test T → T† cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.TDG, [q0]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
        self.assertEqual(opt_pass.metrics.t_gates_removed, 2)
    
    def test_rotation_cancellation(self):
        """Test RZ(θ) → RZ(-θ) cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': 0.5}))
        circuit.add_instruction(QIRInstruction(InstructionType.RZ, [q0], {'theta': -0.5}))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_no_cancellation_different_qubits(self):
        """Test that gates on different qubits don't cancel."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 2)  # No cancellation
    
    def test_no_cancellation_different_gates(self):
        """Test that different gates don't cancel."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 2)  # No cancellation
    
    def test_multiple_cancellations(self):
        """Test multiple cancellations in one circuit."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # H → H (cancel)
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # X (keep)
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q1]))
        
        # CNOT → CNOT (cancel)
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        self.assertEqual(circuit.get_gate_count(), 5)
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 1)  # Only X remains
        self.assertEqual(opt_pass.metrics.gates_removed, 4)
    
    def test_bell_state_with_redundancy(self):
        """Test Bell state circuit with redundant gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # Redundant H at start
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        
        # Actual Bell state
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        # Redundant CNOT at end
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        
        self.assertEqual(circuit.get_gate_count(), 6)
        
        opt_pass = GateCancellationPass()
        result = opt_pass.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 2)  # H and CNOT remain
    
    def test_with_pass_manager(self):
        """Test gate cancellation through pass manager."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        manager = PassManager([GateCancellationPass()])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        self.assertEqual(result.get_gate_count(), 1)  # Only X remains


if __name__ == '__main__':
    unittest.main()
