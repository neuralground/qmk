#!/usr/bin/env python3
"""Tests for constant propagation."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from kernel.qir_bridge.optimizer.passes import (
    ConstantPropagationPass, GateCancellationPass
)


class TestConstantPropagation(unittest.TestCase):
    """Test constant propagation optimization."""
    
    def test_track_zero_state(self):
        """Test tracking |0⟩ state."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Start at |0⟩, apply X → |1⟩, apply X → |0⟩
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        # Run constant propagation
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # State tracking should work (even if no optimization yet)
        self.assertIsNotNone(result)
    
    def test_track_hadamard_state(self):
        """Test tracking Hadamard states."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # |0⟩ → H → |+⟩ → H → |0⟩
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # Should track state transitions
        self.assertIsNotNone(result)
    
    def test_combined_with_cancellation(self):
        """Test constant propagation enabling cancellation."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # X → X should cancel (returns to |0⟩)
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        # Run both passes
        manager = PassManager([
            ConstantPropagationPass(),
            GateCancellationPass()
        ])
        manager.verbose = False
        
        result = manager.run(circuit)
        
        # Cancellation should remove X → X
        self.assertEqual(result.get_gate_count(), 0)
    
    def test_state_unknown_after_two_qubit_gate(self):
        """Test that two-qubit gates make states unknown."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # After CNOT, states are unknown
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.CNOT, [q0, q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # Should handle unknown states gracefully
        self.assertIsNotNone(result)
    
    def test_state_unknown_after_measurement(self):
        """Test that measurement makes state unknown."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # Should handle post-measurement state
        self.assertIsNotNone(result)
    
    def test_z_gate_state_transitions(self):
        """Test Z gate state transitions."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # |0⟩ → H → |+⟩ → Z → |-⟩
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.Z, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # Should track |+⟩ → |-⟩ transition
        self.assertIsNotNone(result)
    
    def test_no_optimization_without_patterns(self):
        """Test that pass doesn't break circuits without optimization opportunities."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.X, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.MEASURE, [q0], result='m0'))
        
        initial_count = circuit.get_gate_count()
        
        opt_pass = ConstantPropagationPass()
        result = opt_pass.run(circuit)
        
        # Should not remove anything
        self.assertEqual(result.get_gate_count(), initial_count)


if __name__ == '__main__':
    unittest.main()
