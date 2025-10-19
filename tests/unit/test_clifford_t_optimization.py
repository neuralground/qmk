#!/usr/bin/env python3
"""Tests for Clifford+T optimization."""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge.optimizer import (
    QIRCircuit, QIRInstruction, InstructionType, PassManager
)
from kernel.qir_bridge.optimizer.passes import CliffordTPlusOptimizationPass


class TestCliffordTOptimization(unittest.TestCase):
    """Test Clifford+T optimization."""
    
    def test_t_four_to_s(self):
        """Test T⁴ → S optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Four T gates = S
        for _ in range(4):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        self.assertEqual(self._count_t_gates(circuit), 4)
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should replace with S
        self.assertEqual(self._count_t_gates(result), 0)
        self.assertEqual(opt_pass.metrics.t_gate_reduction, 4)
        
        # Should have one S gate
        s_count = sum(1 for inst in result.instructions 
                     if inst.inst_type == InstructionType.S)
        self.assertEqual(s_count, 1)
    
    def test_t_eight_to_identity(self):
        """Test T⁸ → Identity optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Eight T gates = Identity
        for _ in range(8):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have 2 S gates (T⁸ = S²)
        self.assertEqual(self._count_t_gates(result), 0)
        self.assertEqual(opt_pass.metrics.t_gate_reduction, 8)
    
    def test_t_five_to_s_plus_t(self):
        """Test T⁵ → S + T optimization."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # Five T gates = S + T
        for _ in range(5):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should have 1 T gate remaining (5 = 4 + 1)
        self.assertEqual(self._count_t_gates(result), 1)
        self.assertEqual(opt_pass.metrics.t_gate_reduction, 4)
    
    def test_commute_t_gates_together(self):
        """Test that T gates are commuted together."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # T(q0) → H(q1) → T(q0) → H(q1) → T(q0) → T(q0)
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q1]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should reduce T count (4 T's → 1 S)
        self.assertLess(self._count_t_gates(result), 4)
    
    def test_no_t_gates(self):
        """Test circuit with no T gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should not change anything
        self.assertEqual(len(result.instructions), 2)
        self.assertEqual(opt_pass.metrics.t_gate_reduction, 0)
    
    def test_t_count_metric(self):
        """Test that T-count metrics are tracked."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        for _ in range(6):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should track initial and final T counts
        self.assertEqual(opt_pass.metrics.custom['initial_t_count'], 6)
        self.assertLess(opt_pass.metrics.custom['final_t_count'], 6)
        self.assertGreater(opt_pass.metrics.custom['t_reduction_percent'], 0)
    
    def test_mixed_clifford_and_t(self):
        """Test circuit with mixed Clifford and T gates."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        
        # H → T → T → S → T → T
        circuit.add_instruction(QIRInstruction(InstructionType.H, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.S, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        
        initial_t = self._count_t_gates(circuit)
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        final_t = self._count_t_gates(result)
        
        # Should reduce T count
        self.assertLessEqual(final_t, initial_t)
    
    def test_t_gates_on_different_qubits(self):
        """Test T gates on different qubits."""
        circuit = QIRCircuit()
        q0 = circuit.add_qubit('q0')
        q1 = circuit.add_qubit('q1')
        
        # T(q0) × 4, T(q1) × 4
        for _ in range(4):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q0]))
        for _ in range(4):
            circuit.add_instruction(QIRInstruction(InstructionType.T, [q1]))
        
        opt_pass = CliffordTPlusOptimizationPass()
        result = opt_pass.run(circuit)
        
        # Should optimize both qubits
        self.assertEqual(self._count_t_gates(result), 0)
        self.assertEqual(opt_pass.metrics.t_gate_reduction, 8)
    
    # Helper method
    def _count_t_gates(self, circuit: QIRCircuit) -> int:
        """Count T gates in circuit."""
        return sum(1 for inst in circuit.instructions 
                  if inst.inst_type == InstructionType.T)


if __name__ == '__main__':
    unittest.main()
